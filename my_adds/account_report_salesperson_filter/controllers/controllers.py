# -*- coding: utf-8 -*-
# from odoo import http


# class AccountReportSalespersonFilter(http.Controller):
#     @http.route('/account_report_salesperson_filter/account_report_salesperson_filter', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/account_report_salesperson_filter/account_report_salesperson_filter/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('account_report_salesperson_filter.listing', {
#             'root': '/account_report_salesperson_filter/account_report_salesperson_filter',
#             'objects': http.request.env['account_report_salesperson_filter.account_report_salesperson_filter'].search([]),
#         })

#     @http.route('/account_report_salesperson_filter/account_report_salesperson_filter/objects/<model("account_report_salesperson_filter.account_report_salesperson_filter"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('account_report_salesperson_filter.object', {
#             'object': obj
#         })

