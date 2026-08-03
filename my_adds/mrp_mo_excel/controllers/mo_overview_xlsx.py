# controllers/mo_overview_xlsx.py
import io
import xlsxwriter
from odoo import http
from odoo.http import content_disposition, request


class MrpMoOverviewXlsxController(http.Controller):

    @http.route('/mrp/mo_overview/xlsx', type='http', auth='user')
    def get_mo_overview_xlsx(self, docids, **kw):
        mo_id = int(docids)
        report_values = request.env['report.mrp.report_mo_overview'].get_report_values(mo_id)
        data = report_values['data']
        summary = data.get('summary', {})

        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheet = workbook.add_worksheet('MO Overview')

        bold = workbook.add_format({'bold': True})
        header_fmt = workbook.add_format({'bold': True, 'bg_color': '#D9D9D9', 'border': 1})
        money_fmt = workbook.add_format({'num_format': '#,##0.00'})
        indent_fmts = {
            lvl: workbook.add_format({'indent': lvl}) for lvl in range(6)
        }

        headers = ['Name', 'Status', 'Quantity', 'UoM', 'Free to Use / On Hand',
                    'Reserved', 'Unit Cost', 'MO Cost', 'Real Cost']
        for col, title in enumerate(headers):
            sheet.write(0, col, title, header_fmt)
        sheet.set_column(0, 0, 40)
        sheet.set_column(1, 8, 16)

        row = [1]  # mutable counter shared across recursion

        def write_line(line, level=0):
            """Write a single MoOverviewLine-equivalent dict as a row."""
            if not line:
                return
            r = row[0]
            fmt = indent_fmts.get(min(level, 5))
            sheet.write(r, 0, line.get('name', ''), fmt)
            sheet.write(r, 1, line.get('formatted_state', '') or '')
            sheet.write(r, 2, line.get('quantity', 0) or 0)
            sheet.write(r, 3, line.get('uom_name', '') or '')

            on_hand = line.get('quantity_on_hand')
            free = line.get('quantity_free')
            if on_hand not in (False, None):
                sheet.write(r, 4, f"{free or 0} / {on_hand or 0}")

            reserved = line.get('quantity_reserved')
            if reserved not in (False, None):
                sheet.write(r, 5, reserved)

            if 'unit_cost' in line:
                sheet.write(r, 6, line.get('unit_cost', 0) or 0, money_fmt)
            sheet.write(r, 7, line.get('mo_cost', 0) or 0, money_fmt)
            sheet.write(r, 8, line.get('real_cost', 0) or 0, money_fmt)
            row[0] += 1

        def write_components(components, level=1):
            for component in components or []:
                write_line(component.get('summary'), level)
                for repl in component.get('replenishments') or []:
                    write_line(repl.get('summary'), level + 1)
                    write_components(repl.get('components'), level + 2)
                    write_operations(repl.get('operations'), level + 2)
                    write_byproducts(repl.get('byproducts'), level + 2)

        def write_operations(operations, level=1):
            if not operations:
                return
            write_line(operations.get('summary'), level)
            for op in operations.get('details') or []:
                write_line(op, level + 1)

        def write_byproducts(byproducts, level=1):
            if not byproducts:
                return
            write_line(byproducts.get('summary'), level)
            for bp in byproducts.get('details') or []:
                write_line(bp, level + 1)

        # Root MO line
        write_line(summary, level=0)
        # Components (recursive tree)
        write_components(data.get('components'), level=1)
        # Top-level operations / byproducts
        write_operations(data.get('operations'), level=1)
        write_byproducts(data.get('byproducts'), level=1)

        workbook.close()
        output.seek(0)

        return request.make_response(
            output.read(),
            headers=[
                ('Content-Type', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'),
                ('Content-Disposition', content_disposition(f"MO_Overview_{summary.get('name', mo_id)}.xlsx")),
            ],
        )