{
    'name': 'MRP MO Overview Excel Export',
    'version': '17.0.1.0.0',
    'category': 'Manufacturing',
    'depends': ['mrp'],
    'external_dependencies': {
        'python': ['xlsxwriter'],
    },
    'assets': {
    'web.assets_backend': [
        'mrp_mo_excel/static/src/components/mo_overview/mo_overview_patch.js',
        'mrp_mo_excel/static/src/components/mo_overview/mo_overview_patch.xml',
    ],
},
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}


    


