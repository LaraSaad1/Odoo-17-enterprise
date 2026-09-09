# -*- coding: utf-8 -*-
{
    'name': "Quotation Offer Report",
    'category': 'Sales',
    'version': '17.0.1.0.0',
    'depends': ['product', 'web'],
    'data': [
        'security/ir.model.access.csv',
        'report/quotation_offer_report_paperformat.xml',
        'report/quotation_offer_report_template.xml',
        'report/quotation_offer_report_actions.xml',
        'wizard/quotation_offer_wizard_views.xml',
        'views/product_template_views.xml',
    ],
    'images': ['static/description/icon.png'],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
