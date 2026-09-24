# -*- coding: utf-8 -*-
{
    'name': 'Telesales',
    'version': '17.0.1.0.0',

    'category': 'Sales/CRM',
    'license': 'LGPL-3',
    'depends': ['crm', 'sale', 'product', 'crm_salesperson_planner'],
    'data': [
        'security/ir.model.access.csv',
        'data/telesales_sequence.xml',
        'views/telesales_customer_views.xml',
        'views/telesales_call_views.xml',
        'views/telesales_menu.xml',
    ],
    'application': False,
    'installable': True,
}
