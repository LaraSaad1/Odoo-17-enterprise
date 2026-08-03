# -*- coding: utf-8 -*-
# from odoo import http


# class MrpMoExcel(http.Controller):
#     @http.route('/mrp_mo_excel/mrp_mo_excel', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/mrp_mo_excel/mrp_mo_excel/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('mrp_mo_excel.listing', {
#             'root': '/mrp_mo_excel/mrp_mo_excel',
#             'objects': http.request.env['mrp_mo_excel.mrp_mo_excel'].search([]),
#         })

#     @http.route('/mrp_mo_excel/mrp_mo_excel/objects/<model("mrp_mo_excel.mrp_mo_excel"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('mrp_mo_excel.object', {
#             'object': obj
#         })

