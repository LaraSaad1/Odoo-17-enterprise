# -*- coding: utf-8 -*-
import datetime
from itertools import chain

from dateutil.relativedelta import relativedelta

from odoo import models, fields, _
from odoo.exceptions import UserError


class AgedPartnerBalanceCustomHandler(models.AbstractModel):
    """
    Replaces Odoo's stock aging buckets - which are ALWAYS evenly spaced
    (30/30/30/30/Older) - with fixed, unevenly spaced buckets:
    1-30, 31-90, 91-150, 151-365, Older.

    Ported to match Odoo 17's actual account_reports API (odoo 17 does NOT
    have odoo.tools.SQL, report._get_report_query, _currency_table_apply_rate,
    or options['aging_based_on'] - all of those are Odoo 18-only and were
    causing AttributeError / KeyError when this module was first ported).

    _CUMULATIVE_DAYS is the single source of truth for the bucket edges:
    both the report's data engine and its "click a cell to see the
    invoices" audit action read from it, so they can never drift out of
    sync with each other.

    _CUMULATIVE_DAYS[0] is always 0. Each subsequent value is the
    cumulative day-count at which that bucket ends. The number of entries
    after the leading 0 must equal the number of dated columns
    (period1..period4) defined on the Aged Receivable / Aged Payable
    reports - 4, by default in stock Odoo 17 (5 periods total: period0
    "Not Due" + 4 aging buckets... adjusted below to also support the
    stock 6-period layout: period0 Not Due + period1..period4 + Older).
    """
    _inherit = 'account.aged.partner.balance.report.handler'

    _CUMULATIVE_DAYS = [0, 30, 90, 150, 365]  # -> buckets: 1-30, 31-90, 91-150, 151-365, then Older

    # ------------------------------------------------------------------
    # Column labels ("1 - 30", "31 - 90", ...)
    # ------------------------------------------------------------------
    def _custom_options_initializer(self, report, options, previous_options=None):
        super()._custom_options_initializer(report, options, previous_options=previous_options)

        # Toggle state, persisted per user/session. Defaults to ON.
        options['custom_periods_enabled'] = (
            True if previous_options is None
            else previous_options.get('custom_periods_enabled', True)
        )

        if not options['custom_periods_enabled']:
            return  # leave the stock interval-based labels super() already set

        custom_labels = []
        prev = 0
        for end_day in self._CUMULATIVE_DAYS[1:]:
            custom_labels.append(f'{prev + 1} - {end_day}')
            prev = end_day

        for column in options['columns']:
            if column['expression_label'].startswith('period'):
                period_number = int(column['expression_label'].replace('period', '')) - 1
                if 0 <= period_number < len(custom_labels):
                    column['name'] = custom_labels[period_number]

    # ------------------------------------------------------------------
    # Core data engine - rebuilt against Odoo 17's actual account_reports
    # API (report._query_get / report._get_query_currency_table / raw
    # %s-parameterized SQL). Only the `periods` construction block differs
    # from stock; everything else mirrors the v17 original method exactly.
    # ------------------------------------------------------------------
    def _aged_partner_report_custom_engine_common(self, options, internal_type, current_groupby, next_groupby, offset=0, limit=None):
        report = self.env['account.report'].browse(options['report_id'])
        report._check_groupby_fields((next_groupby.split(',') if next_groupby else []) + ([current_groupby] if current_groupby else []))

        def minus_days(date_obj, days):
            return fields.Date.to_string(date_obj - relativedelta(days=days))

        date_to = fields.Date.from_string(options['date']['date_to'])
        nb_periods = len([column for column in options['columns'] if column['expression_label'].startswith('period')]) - 1

        if options.get('custom_periods_enabled', True):
            # --- CUSTOM: variable-width buckets instead of the stock 30/30/30/30 spacing ---
            bounds = self._CUMULATIVE_DAYS[1:]  # e.g. [30, 90, 150, 365]
            if nb_periods != len(bounds) + 1:
                raise UserError(_(
                    "Aged Report Custom Periods: the report defines %(actual)s dated "
                    "period columns, but this module's _CUMULATIVE_DAYS expects "
                    "%(expected)s (one per custom bucket + Older). Check the "
                    "aged_receivable_report/aged_payable_report column definitions, "
                    "or adjust _CUMULATIVE_DAYS to match.",
                    actual=nb_periods, expected=len(bounds) + 1,
                ))

            periods = [(False, fields.Date.to_string(date_to))]  # period0: Not Due
            prev_end = 0
            for end_day in bounds:
                start_date = minus_days(date_to, prev_end + 1)
                end_date = minus_days(date_to, end_day)
                periods.append((start_date, end_date))
                prev_end = end_day
            periods.append((minus_days(date_to, prev_end + 1), False))  # Older, open-ended
            # --- END CUSTOM ---
        else:
            # --- STOCK: original hardcoded 30/30/30/30/Older layout ---
            periods = [
                (False, fields.Date.to_string(date_to)),
                (minus_days(date_to, 1), minus_days(date_to, 30)),
                (minus_days(date_to, 31), minus_days(date_to, 60)),
                (minus_days(date_to, 61), minus_days(date_to, 90)),
                (minus_days(date_to, 91), minus_days(date_to, 120)),
                (minus_days(date_to, 121), False),
            ]
            # --- END STOCK ---

        def build_result_dict(report, query_res_lines):
            rslt = {f'period{i}': 0 for i in range(len(periods))}

            for query_res in query_res_lines:
                for i in range(len(periods)):
                    period_key = f'period{i}'
                    rslt[period_key] += query_res[period_key]

            if current_groupby == 'id':
                query_res = query_res_lines[0]  # We're grouping by id, so there is only 1 element in query_res_lines anyway
                currency = self.env['res.currency'].browse(query_res['currency_id'][0]) if len(query_res['currency_id']) == 1 else None
                expected_date = len(query_res['expected_date']) == 1 and query_res['expected_date'][0] or len(query_res['due_date']) == 1 and query_res['due_date'][0]
                rslt.update({
                    'invoice_date': query_res['invoice_date'][0] if len(query_res['invoice_date']) == 1 else None,
                    'due_date': query_res['due_date'][0] if len(query_res['due_date']) == 1 else None,
                    'amount_currency': query_res['amount_currency'],
                    'currency_id': query_res['currency_id'][0] if len(query_res['currency_id']) == 1 else None,
                    'currency': currency.display_name if currency else None,
                    'account_name': query_res['account_name'][0] if len(query_res['account_name']) == 1 else None,
                    'expected_date': expected_date or None,
                    'total': None,
                    'has_sublines': query_res['aml_count'] > 0,
                    'partner_id': query_res['partner_id'][0] if query_res['partner_id'] else None,
                })
            else:
                rslt.update({
                    'invoice_date': None,
                    'due_date': None,
                    'amount_currency': None,
                    'currency_id': None,
                    'currency': None,
                    'account_name': None,
                    'expected_date': None,
                    'total': sum(rslt[f'period{i}'] for i in range(len(periods))),
                    'has_sublines': False,
                })

            return rslt

        # Build period table
        period_table_format = ('(VALUES %s)' % ','.join("(%s, %s, %s)" for period in periods))
        params = list(chain.from_iterable(
            (period[0] or None, period[1] or None, i)
            for i, period in enumerate(periods)
        ))
        period_table = self.env.cr.mogrify(period_table_format, params).decode(self.env.cr.connection.encoding)

        # Build query
        tables, where_clause, where_params = report._query_get(options, 'strict_range', domain=[('account_id.account_type', '=', internal_type)])

        currency_table = report._get_query_currency_table(options)
        always_present_groupby = "period_table.period_index, currency_table.rate, currency_table.precision"
        if current_groupby:
            select_from_groupby = f"account_move_line.{current_groupby} AS grouping_key,"
            groupby_clause = f"account_move_line.{current_groupby}, {always_present_groupby}"
        else:
            select_from_groupby = ''
            groupby_clause = always_present_groupby
        select_period_query = ','.join(
            f"""
                CASE WHEN period_table.period_index = {i}
                THEN %s * (
                    SUM(ROUND(account_move_line.balance * currency_table.rate, currency_table.precision))
                    - COALESCE(SUM(ROUND(part_debit.amount * currency_table.rate, currency_table.precision)), 0)
                    + COALESCE(SUM(ROUND(part_credit.amount * currency_table.rate, currency_table.precision)), 0)
                )
                ELSE 0 END AS period{i}
            """
            for i in range(len(periods))
        )

        tail_query, tail_params = report._get_engine_query_tail(offset, limit)
        query = f"""
            WITH period_table(date_start, date_stop, period_index) AS ({period_table})

            SELECT
                {select_from_groupby}
                %s * (
                    SUM(account_move_line.amount_currency)
                    - COALESCE(SUM(part_debit.debit_amount_currency), 0)
                    + COALESCE(SUM(part_credit.credit_amount_currency), 0)
                ) AS amount_currency,
                ARRAY_AGG(DISTINCT account_move_line.partner_id) AS partner_id,
                ARRAY_AGG(account_move_line.payment_id) AS payment_id,
                ARRAY_AGG(DISTINCT move.invoice_date) AS invoice_date,
                ARRAY_AGG(DISTINCT COALESCE(account_move_line.date_maturity, account_move_line.date)) AS report_date,
                ARRAY_AGG(DISTINCT account_move_line.expected_pay_date) AS expected_date,
                ARRAY_AGG(DISTINCT account.code) AS account_name,
                ARRAY_AGG(DISTINCT COALESCE(account_move_line.date_maturity, account_move_line.date)) AS due_date,
                ARRAY_AGG(DISTINCT account_move_line.currency_id) AS currency_id,
                COUNT(account_move_line.id) AS aml_count,
                ARRAY_AGG(account.code) AS account_code,
                {select_period_query}

            FROM {tables}

            JOIN account_journal journal ON journal.id = account_move_line.journal_id
            JOIN account_account account ON account.id = account_move_line.account_id
            JOIN account_move move ON move.id = account_move_line.move_id
            JOIN {currency_table} ON currency_table.company_id = account_move_line.company_id

            LEFT JOIN LATERAL (
                SELECT
                    SUM(part.amount) AS amount,
                    SUM(part.debit_amount_currency) AS debit_amount_currency,
                    part.debit_move_id
                FROM account_partial_reconcile part
                WHERE part.max_date <= %s AND part.debit_move_id = account_move_line.id
                GROUP BY part.debit_move_id
            ) part_debit ON TRUE

            LEFT JOIN LATERAL (
                SELECT
                    SUM(part.amount) AS amount,
                    SUM(part.credit_amount_currency) AS credit_amount_currency,
                    part.credit_move_id
                FROM account_partial_reconcile part
                WHERE part.max_date <= %s AND part.credit_move_id = account_move_line.id
                GROUP BY part.credit_move_id
            ) part_credit ON TRUE

            JOIN period_table ON
                (
                    period_table.date_start IS NULL
                    OR COALESCE(account_move_line.date_maturity, account_move_line.date) <= DATE(period_table.date_start)
                )
                AND
                (
                    period_table.date_stop IS NULL
                    OR COALESCE(account_move_line.date_maturity, account_move_line.date) >= DATE(period_table.date_stop)
                )

            WHERE {where_clause}

            GROUP BY {groupby_clause}

            HAVING
                (
                    SUM(ROUND(CASE WHEN account_move_line.balance > 0  THEN account_move_line.balance else 0 END * currency_table.rate, currency_table.precision))
                    - COALESCE(SUM(ROUND(part_debit.amount * currency_table.rate, currency_table.precision)), 0)
                ) != 0
                OR
                (
                    SUM(ROUND(CASE WHEN account_move_line.balance < 0  THEN -account_move_line.balance else 0 END * currency_table.rate, currency_table.precision))
                    - COALESCE(SUM(ROUND(part_credit.amount * currency_table.rate, currency_table.precision)), 0)
                ) != 0
            {tail_query}
        """

        multiplicator = -1 if internal_type == 'liability_payable' else 1
        params = [
            multiplicator,
            *([multiplicator] * len(periods)),
            date_to,
            date_to,
            *where_params,
            *tail_params,
        ]
        self._cr.execute(query, params)
        query_res_lines = self._cr.dictfetchall()

        if not current_groupby:
            return build_result_dict(report, query_res_lines)
        else:
            rslt = []

            all_res_per_grouping_key = {}
            for query_res in query_res_lines:
                grouping_key = query_res['grouping_key']
                all_res_per_grouping_key.setdefault(grouping_key, []).append(query_res)

            for grouping_key, query_res_lines in all_res_per_grouping_key.items():
                rslt.append((grouping_key, build_result_dict(report, query_res_lines)))

            return rslt

    # ------------------------------------------------------------------
    # Audit / drill-down domain when a cell is clicked. Stock Odoo
    # hardcodes 30-day buckets here regardless of the interval - it must
    # be kept in sync with the buckets above or the invoices shown won't
    # match the cell that was clicked.
    # ------------------------------------------------------------------
    def _build_domain_from_period(self, options, period):
        if period == "total" or not period[-1].isdigit():
            return []

        period_number = int(period[-1])
        options_date_to = datetime.datetime.strptime(options['date']['date_to'], '%Y-%m-%d')

        if period_number == 0:
            return [('date_maturity', '>=', options['date']['date_to'])]

        if not options.get('custom_periods_enabled', True):
            # --- STOCK: original hardcoded-30-day formula ---
            period_end = options_date_to - datetime.timedelta(30 * (period_number - 1) + 1)
            period_start = options_date_to - datetime.timedelta(30 * period_number)
            if period_number == 5:
                return [('date_maturity', '<=', period_end)]
            return [('date_maturity', '>=', period_start), ('date_maturity', '<=', period_end)]

        bounds = self._CUMULATIVE_DAYS  # [0, 30, 90, 150, 365]

        if 1 <= period_number < len(bounds):
            days_before = bounds[period_number - 1]
            days_after = bounds[period_number]
            period_start = options_date_to - datetime.timedelta(days=days_after)
            period_end = options_date_to - datetime.timedelta(days=days_before + 1)
            return [('date_maturity', '>=', period_start), ('date_maturity', '<=', period_end)]

        # Older: anything past the last defined boundary
        period_end = options_date_to - datetime.timedelta(days=bounds[-1] + 1)
        return [('date_maturity', '<=', period_end)]