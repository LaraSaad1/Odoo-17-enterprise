from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class QualityInspectionTemplate(models.Model):
    _name = 'quality.inspection.template'
    _description = 'Quality Inspection Template'
    _order = 'sequence, id'

    name = fields.Char('Inspection Name', required=True)
    sequence = fields.Integer('Sequence', default=10)
    active = fields.Boolean(default=True)
    
    # Link to existing product.category
    product_category_id = fields.Many2one(
        'product.category',
        'Product Category',
        required=True,
        help="The product category this inspection field belongs to"
    )
    
    field_type = fields.Selection([
        ('char', 'Text'),
        ('float', 'Number/Measurement'),
        ('integer', 'Integer'),
        ('selection', 'Selection'),
        ('boolean', 'Pass/Fail'),
        ('text', 'Long Text'),
        ('date', 'Date'),
    ], string='Field Type', required=True, default='float')
    
    selection_options = fields.Char('Selection Options')
    min_value = fields.Float('Minimum Value')
    max_value = fields.Float('Maximum Value')
    required = fields.Boolean('Required', default=True)
    uom_id = fields.Many2one('uom.uom', 'Unit of Measure')
    help_text = fields.Char('Help Text')

    @api.constrains('min_value', 'max_value')
    def _check_min_max(self):
        for template in self:
            if template.min_value and template.max_value:
                if template.min_value > template.max_value:
                    raise ValidationError(_("Minimum value cannot be greater than maximum value."))