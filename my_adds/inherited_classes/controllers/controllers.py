# -*- coding: utf-8 -*-
# from odoo import http


# class InheritedClasses(http.Controller):
#     @http.route('/inherited_classes/inherited_classes', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/inherited_classes/inherited_classes/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('inherited_classes.listing', {
#             'root': '/inherited_classes/inherited_classes',
#             'objects': http.request.env['inherited_classes.inherited_classes'].search([]),
#         })

#     @http.route('/inherited_classes/inherited_classes/objects/<model("inherited_classes.inherited_classes"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('inherited_classes.object', {
#             'object': obj
#         })

