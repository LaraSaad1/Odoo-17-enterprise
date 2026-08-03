import io
import base64
import xlsxwriter

from odoo import models, api


class ReportMoOverview(models.AbstractModel):
    _inherit = 'report.mrp.report_mo_overview'

    @api.model
    def action_export_excel(self, docids, show_options=None, unfolded_ids=None):
        show_options = show_options or {}
        data = {'doc_ids': docids, 'doc_model': 'mrp.production'}
        report_values = self._get_report_values(docids, data)
        data_dict = report_values.get('data', {})
        summary = data_dict.get('summary', {})
        extras = data_dict.get('extras', {})
        cost_breakdown = data_dict.get('cost_breakdown', [])

        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})

        bold = workbook.add_format({'bold': True})
        header = workbook.add_format({
            'bold': True, 'bg_color': '#E2E2E2', 'border': 1,
            'align': 'center', 'valign': 'vcenter'
        })
        money = workbook.add_format({'num_format': '#,##0.00', 'align': 'right'})
        right = workbook.add_format({'align': 'right'})
        center = workbook.add_format({'align': 'center'})

        # Sheet 1: Overview
        sheet1 = workbook.add_worksheet('MO Overview')
        sheet1.write('A1', 'Manufacturing Order Overview', bold)
        sheet1.write('A2', 'Product:', bold)
        sheet1.write('B2', summary.get('name', ''))
        sheet1.write('A3', 'Quantity:', bold)
        sheet1.write('B3', summary.get('quantity', ''))
        if summary.get('uom_name'):
            sheet1.write('C3', summary.get('uom_name'))

        row = 5
        headers = ['Description']
        if show_options.get('replenishments'):
            headers.append('Status')
        headers.append('Quantity')
        if show_options.get('availabilities'):
            headers.extend(['Free to use / On Hand', 'Reserved'])
        if show_options.get('receipts'):
            headers.append('Receipt')
        if show_options.get('unitCosts'):
            headers.append('Unit Cost')
        if show_options.get('moCosts'):
            headers.append('MO Cost')
        if show_options.get('realCosts'):
            headers.append('Real Cost')

        for col, h in enumerate(headers):
            sheet1.write(row, col, h, header)

        row += 1
        sheet1.write(row, 0, summary.get('name', ''))
        col_idx = 1
        if show_options.get('replenishments'):
            sheet1.write(row, col_idx, summary.get('status', ''), center)
            col_idx += 1
        sheet1.write(row, col_idx, summary.get('quantity', 0), right)
        col_idx += 1
        if show_options.get('availabilities'):
            sheet1.write(row, col_idx, summary.get('free_to_use_qty', 0), right)
            col_idx += 1
            sheet1.write(row, col_idx, summary.get('reserved_qty', 0), right)
            col_idx += 1
        if show_options.get('receipts'):
            sheet1.write(row, col_idx, summary.get('receipt_qty', 0), right)
            col_idx += 1
        if show_options.get('unitCosts'):
            sheet1.write(row, col_idx, extras.get('unit_mo_cost', 0), money)
            col_idx += 1
        if show_options.get('moCosts'):
            sheet1.write(row, col_idx, extras.get('unit_mo_cost', 0), money)
            col_idx += 1
        if show_options.get('realCosts'):
            sheet1.write(row, col_idx, extras.get('unit_real_cost', 0), money)
            col_idx += 1

        if summary.get('state') == 'done':
            row += 2
            sheet1.write(row, 0, 'Unit Cost', bold)
            if show_options.get('moCosts'):
                sheet1.write(row, col_idx - 2 if show_options.get('realCosts') else col_idx - 1,
                             extras.get('unit_mo_cost', 0), money)
            if show_options.get('realCosts'):
                sheet1.write(row, col_idx - 1, extras.get('unit_real_cost', 0), money)

        for i in range(len(headers)):
            sheet1.set_column(i, i, 18)

        # Sheet 2: Cost Breakdown
        if cost_breakdown:
            sheet2 = workbook.add_worksheet('Cost Breakdown')
            bd_headers = ['Product', 'Avg Cost of Components per Unit']
            if data_dict.get('operations', {}).get('details'):
                bd_headers.append('Avg Cost of Operations per Unit')
            bd_headers.append('Avg Total Cost per Unit')
            if show_options.get('uom'):
                bd_headers.append('Unit of Measure')

            for col, h in enumerate(bd_headers):
                sheet2.write(0, col, h, header)

            for r, line in enumerate(cost_breakdown, start=1):
                c = 0
                sheet2.write(r, c, line.get('name', '')); c += 1
                sheet2.write(r, c, line.get('unit_avg_cost_component', 0), money); c += 1
                if data_dict.get('operations', {}).get('details'):
                    sheet2.write(r, c, line.get('unit_avg_cost_operation', 0), money); c += 1
                sheet2.write(r, c, line.get('unit_avg_total_cost', 0), money); c += 1
                if show_options.get('uom'):
                    sheet2.write(r, c, line.get('uom_name', '')); c += 1

            for i in range(len(bd_headers)):
                sheet2.set_column(i, i, 22)

        workbook.close()
        output.seek(0)
        file_data = base64.b64encode(output.read())

        mo = self.env['mrp.production'].browse(docids[0])
        attachment = self.env['ir.attachment'].create({
            'name': 'MO_Overview_%s.xlsx' % (mo.name or docids[0]),
            'type': 'binary',
            'datas': file_data,
            'res_model': 'mrp.production',
            'res_id': docids[0],
        })

        return {
            'type': 'ir.actions.act_url',
            'url': '/web/content/%s?download=1' % attachment.id,
            'target': 'self',
        }