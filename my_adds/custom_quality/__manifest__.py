{
    'name': 'Custom Quality Inspection',
    'version': '17.0.1.0.0',
    'category': 'Quality',
    'depends': [
        'quality',
        'quality_control',
        'stock',
        'product',
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/quality_inspection_templates.xml',
        'views/quality_point_views.xml',
        'views/quality_inspection_views.xml',
    ],
    'installable': True,
    'license': 'LGPL-3',
}