from odoo import models, fields, api

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    formulation = fields.Char(
        string='المادة الفعالة',
    )

    pests = fields.Char(
        string='الآفة',
    )

    crop = fields.Char(
        string='المحصول',
    )
