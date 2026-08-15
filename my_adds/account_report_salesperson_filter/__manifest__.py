{
    'name': 'Partner Ledger - Salesperson Filter',
    'version': '17.0.1.0.0',
    'summary': 'Adds a Salesperson filter to the Partner Ledger (and other partner-filterable reports)',
    'depends': ['account_reports'],
    'data': [],
    'assets': {
        'web.assets_backend': [
            'account_report_salesperson_filter/static/src/xml/account_report_filter_partner_salesperson.xml',
        ],
    },
    'installable': True,
    'license': 'LGPL-3',
}