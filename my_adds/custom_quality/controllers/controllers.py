# -*- coding: utf-8 -*-
# from odoo import http


# class CustomQuality(http.Controller):
#     @http.route('/custom_quality/custom_quality', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/custom_quality/custom_quality/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('custom_quality.listing', {
#             'root': '/custom_quality/custom_quality',
#             'objects': http.request.env['custom_quality.custom_quality'].search([]),
#         })

#     @http.route('/custom_quality/custom_quality/objects/<model("custom_quality.custom_quality"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('custom_quality.object', {
#             'object': obj
#         })

