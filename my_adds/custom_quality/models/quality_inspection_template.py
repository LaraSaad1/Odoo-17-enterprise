from odoo import models, fields, api


class QualityInspectionTemplate(models.Model):
    _name = 'quality.inspection.template'
    _description = 'Quality Inspection Form'
    _order = 'id'

    name = fields.Char(
        string='Inspection Form Name',
        required=True,
    )

    product_category_id = fields.Many2one(
        'product.category',
        string='Product Category',
        required=True,
        ondelete='restrict',
    )

    inspection_field_ids = fields.One2many(
        'quality.inspection.template.field',
        'template_id',
        string='Inspection Fields',
        copy=True,
    )

    field_count = fields.Integer(
        string='Field Count',
        compute='_compute_field_count',
        store=True,
    )

    @api.depends('inspection_field_ids')
    def _compute_field_count(self):
        for template in self:
            template.field_count = len(template.inspection_field_ids)


class QualityInspectionTemplateField(models.Model):
    _name = 'quality.inspection.template.field'
    _description = 'Quality Inspection Form Field'
    _order = 'sequence, id'

    product_category_id = fields.Many2one('product.category', string='Product Category')

    template_id = fields.Many2one(
        'quality.inspection.template',
        string='Inspection Form',
        required=True,
        ondelete='cascade',
    )

    name = fields.Char(
        string='Inspection Name',
        required=True,
    )

    test_type_id = fields.Many2one(
        'quality.point.test_type',
        string='Test Type',
    )

    required = fields.Boolean(
        string='Required',
        default=True,
    )

    help_text = fields.Char(
        string='Help Text',
    )

    sequence = fields.Integer(
        string='Sequence',
        default=10,
    )