from odoo import models


class AccountReportPartnerSalespersonFilter(models.Model):
    _inherit = 'account.report'

    def _init_options_partner(self, options, previous_options=None):
        super()._init_options_partner(options, previous_options=previous_options)

        # Always set the key, even if filter_partner is falsy, so the frontend
        # widget never receives 'undefined' for options.partner_users.
        if not self.filter_partner:
            options.setdefault('partner_users', [])
            return

        previous_partner_user_ids = previous_options and previous_options.get('partner_users') or []
        options['partner_users'] = previous_partner_user_ids

        selected_user_ids = [int(u) for u in previous_partner_user_ids]
        selected_users = (
            self.env['res.users'].browse(selected_user_ids)
            if selected_user_ids else self.env['res.users']
        )
        options['selected_partner_users'] = selected_users.mapped('name')

    def _get_options_partner_domain(self, options):
        domain = super()._get_options_partner_domain(options)

        if options.get('partner_users'):
            partner_user_ids = [int(u) for u in options['partner_users']]
          
            domain.append(('move_id.invoice_user_id', 'in', partner_user_ids))

        return domain


