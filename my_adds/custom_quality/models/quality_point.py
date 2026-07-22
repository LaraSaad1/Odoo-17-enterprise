from odoo import models, fields, api, _
from odoo.exceptions import UserError


class QualityPoint(models.Model):
    _inherit = 'quality.point'

    # The inspection fields that define the form on this control point
    inspection_field_ids = fields.One2many(
        'quality.point.inspection.field',
        'point_id',
        string='Inspection Fields'
    )
    
    is_multi_field = fields.Boolean(
        'Multi-Field Inspection',
        default=False,
        help="Enable form with multiple inspection fields"
    )

    @api.onchange('product_ids')
    def _onchange_product_ids_get_categories(self):
        if self.product_ids:
            categories = self.product_ids.mapped('categ_id')
            if categories:
                existing_categories = self.product_category_ids.ids
                combined_ids = list(set(existing_categories) | set(categories.ids))
                self.product_category_ids = [(6, 0, combined_ids)]
            
    def action_load_inspection_fields(self):
        """Load inspection fields based on selected product categories"""
        self.ensure_one()
        
        if not self.product_category_ids:
            raise UserError(_("Please select at least one product category first."))
        
        # Get templates for ALL selected categories
        templates = self.env['quality.inspection.template'].search([
            ('product_category_id', 'in', self.product_category_ids.ids),
            ('active', '=', True)
        ], order='id')
        
        if not templates:
            raise UserError(_("No inspection templates found for the selected product categories. Please configure them in Quality > Configuration > Inspection Templates."))
        
        # Clear existing and load new
        self.inspection_field_ids.unlink()
        
        lines = []
        for template in templates:
            lines.append((0, 0, {
                'template_id': template.id,
                'name': template.name,
                'min_value': template.min_value,
                'max_value': template.max_value,
                'required': template.required,
                'uom_id': template.uom_id.id,
              
                'product_category_id': template.product_category_id.id,
            }))
        
        self.inspection_field_ids = lines
        self.is_multi_field = True
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Success'),
                'message': _('%s inspection fields loaded from %s categories, Kindly refresh the page') % (
                    len(templates), 
                    len(self.product_category_ids)
                ),
                'type': 'success',
            }
        }


class QualityPointInspectionField(models.Model):
    _name = 'quality.point.inspection.field'
    _description = 'Quality Point Inspection Field'


    point_id = fields.Many2one('quality.point', 'Quality Point', required=True, ondelete='cascade')
    template_id = fields.Many2one('quality.inspection.template', 'Template')
    
    # Link to the product category this field belongs to
    product_category_id = fields.Many2one('product.category', 'Product Category', readonly=True)
    
    name = fields.Char('Field Name', required=True)
   
    min_value = fields.Float('Minimum Value')
    max_value = fields.Float('Maximum Value')
    required = fields.Boolean('Required', default=True)
    uom_id = fields.Many2one('uom.uom', 'Unit of Measure')