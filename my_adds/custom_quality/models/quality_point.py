from odoo import models, fields, api, _
from odoo.exceptions import UserError


class QualityPoint(models.Model):
    _inherit = 'quality.point'

    inspection_template_ids = fields.Many2many(
        'quality.inspection.template',
        'quality_point_inspection_template_rel',
        'point_id',
        'template_id',
        string='Inspection Forms',
        help='Inspection forms that will be used for this Quality Control Point.',
    )

    inspection_field_ids = fields.One2many(
        'quality.point.inspection.field',
        'point_id',
        string='Inspection Fields',
    )

    is_multi_field = fields.Boolean(
        string='Multi-Field Inspection',
        default=False,
        help='Enable custom multi-field inspection.',
    )

    @api.onchange('product_ids')
    def _onchange_product_ids_get_categories(self):
        """
        Automatically adds the categories of the selected products
        to the existing product categories on the Quality Point.
        """
        if self.product_ids:
            categories = self.product_ids.mapped('categ_id')

            if categories:
                existing_categories = self.product_category_ids.ids

                combined_ids = list(
                    set(existing_categories) | set(categories.ids)
                )

                self.product_category_ids = [
                    (6, 0, combined_ids)
                ]

    @api.onchange('product_category_ids')
    def _onchange_product_category_ids_get_templates(self):
        """
        Automatically find inspection templates that belong to
        the selected product categories.
        """
        if not self.product_category_ids:
            self.inspection_template_ids = [(5, 0, 0)]
            return

        templates = self.env[
            'quality.inspection.template'
        ].search([
            (
                'product_category_id',
                'in',
                self.product_category_ids.ids,
            ),
        ])

        self.inspection_template_ids = [
            (6, 0, templates.ids)
        ]

    def action_load_inspection_fields(self):
        """
        Load all fields from all selected inspection forms
        into this Quality Control Point.

        The product category is copied from the inspection template
        to each inspection field, just like the old version.
        """
        self.ensure_one()

        if not self.product_category_ids:
            raise UserError(
                _(
                    'Please select at least one product category first.'
                )
            )

        if not self.inspection_template_ids:
            raise UserError(
                _(
                    'No inspection forms are configured for '
                    'the selected product categories.'
                )
            )

        # Remove previously loaded fields
        self.inspection_field_ids.unlink()

        lines = []

        for template in self.inspection_template_ids:

            for template_field in template.inspection_field_ids:

                lines.append(
                    (
                        0,
                        0,
                        {
                            'template_id': template.id,
                            'template_field_id': template_field.id,
                            'product_category_id': (
                                template.product_category_id.id
                            ),
                            'name': template_field.name,
                            'test_type_id': (
                                template_field.test_type_id.id
                            ),
                            'required': template_field.required,
                            'help_text': template_field.help_text,
                            'sequence': template_field.sequence,
                        },
                    )
                )

        if not lines:
            raise UserError(
                _(
                    'The selected inspection forms do not contain '
                    'any inspection fields.'
                )
            )

        self.inspection_field_ids = lines

        self.is_multi_field = True

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'tag': 'reload',
            'params': {
                'title': _('Success'),
                'message': _(
                    '%s inspection fields loaded from %s inspection forms'
                ) % (
                    len(lines),
                    len(self.inspection_template_ids),
                ),
                'type': 'success',
            },
        }


class QualityPointInspectionField(models.Model):
    _name = 'quality.point.inspection.field'
    _description = 'Quality Point Inspection Field'
    _order = 'sequence, id'

    point_id = fields.Many2one(
        'quality.point',
        string='Quality Point',
        required=True,
        ondelete='cascade',
    )

    template_id = fields.Many2one(
        'quality.inspection.template',
        string='Inspection Form',
        readonly=True,
        ondelete='set null',
    )

    template_field_id = fields.Many2one(
        'quality.inspection.template.field',
        string='Template Field',
        readonly=True,
        ondelete='set null',
    )

    product_category_id = fields.Many2one(
        'product.category',
        string='Product Category',
        readonly=True,
        ondelete='set null',
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