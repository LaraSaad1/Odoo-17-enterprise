from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class QualityInspection(models.Model):
    _name = 'custom.quality.inspection'
    _description = 'Custom Quality Inspection'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(
        string='Inspection Reference',
        required=True,
        readonly=True,
        default=lambda self: _('New'),
    )

    quality_check_id = fields.Many2one(
        'quality.check',
        string='Quality Check',
        required=True,
        readonly=True,
        ondelete='cascade',
    )

    quality_point_id = fields.Many2one(
        'quality.point',
        string='Quality Control Point',
        related='quality_check_id.point_id',
        readonly=True,
    )

    product_id = fields.Many2one(
        'product.product',
        string='Product',
        related='quality_check_id.product_id',
        readonly=True,
    )

    state = fields.Selection(
        [
            ('draft', 'Draft'),
            ('pass', 'Passed'),
            ('fail', 'Failed'),
        ],
        string='Status',
        default='draft',
        tracking=True,
    )

    inspection_line_ids = fields.One2many(
        'custom.quality.inspection.line',
        'inspection_id',
        string='Inspection Fields',
    )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code(
                    'custom.quality.inspection'
                ) or _('New')

        inspections = super().create(vals_list)

        for inspection in inspections:
            inspection._load_inspection_fields()

        return inspections

    def _load_inspection_fields(self):
        """
        Create inspection result lines from the inspection fields
        configured on the Quality Control Point.
        """
        self.ensure_one()

        point = self.quality_point_id

        if not point:
            raise UserError(
                _('The Quality Check is not linked to a Quality Control Point.')
            )

        if not point.is_multi_field:
            raise UserError(
                _('This Quality Control Point is not configured for Multi-Field Inspection.')
            )

        if not point.inspection_field_ids:
            raise UserError(
                _(
                    'The Quality Control Point "%s" has no inspection fields configured.'
                ) % point.display_name
            )

        lines = []

        for field in point.inspection_field_ids:
            lines.append(
                (
                    0,
                    0,
                    {
                        'inspection_field_id': field.id,
                        'template_id': field.template_id.id,
                        'name': field.name,
                        'field_type': field.template_id.field_type,
                        'selection_options': field.template_id.selection_options,
                        'min_value': field.min_value,
                        'max_value': field.max_value,
                        'required': field.required,
                        'uom_id': field.uom_id.id,
                        'product_category_id': field.product_category_id.id,
                    },
                )
            )

        self.inspection_line_ids = lines

    def action_pass(self):
        """
        Mark the custom inspection as passed and update
        the original Odoo quality.check.
        """
        for inspection in self:
            inspection._validate_required_fields()

            inspection.state = 'pass'

            if inspection.quality_check_id:
                inspection.quality_check_id.do_pass()

        return {'type': 'ir.actions.act_window_close'}

    def action_fail(self):
        """
        Mark the custom inspection as failed and update
        the original Odoo quality.check.
        """
        for inspection in self:
            inspection._validate_required_fields()

            inspection.state = 'fail'

            if inspection.quality_check_id:
                inspection.quality_check_id.do_fail()

        return {'type': 'ir.actions.act_window_close'}

    def _validate_required_fields(self):
        self.ensure_one()

        for line in self.inspection_line_ids:
            if not line.required:
                continue

            if line.field_type in ('char', 'text'):
                if not line.value_char:
                    raise ValidationError(
                        _(
                            'The field "%s" is required.'
                        ) % line.name
                    )

            elif line.field_type == 'float':
                if line.value_float is False or line.value_float is None:
                    raise ValidationError(
                        _(
                            'The field "%s" is required.'
                        ) % line.name
                    )

            elif line.field_type == 'integer':
                if line.value_integer is False or line.value_integer is None:
                    raise ValidationError(
                        _(
                            'The field "%s" is required.'
                        ) % line.name
                    )

            elif line.field_type == 'date':
                if not line.value_date:
                    raise ValidationError(
                        _(
                            'The field "%s" is required.'
                        ) % line.name
                    )

            # elif line.field_type == 'selection':
            #     if not line.value_selection:
            #         raise ValidationError(
            #             _(
            #                 'The field "%s" is required.'
            #             ) % line.name
            #         )


class QualityInspectionLine(models.Model):
    _name = 'custom.quality.inspection.line'
    _description = 'Custom Quality Inspection Line'
    _order = 'id'

    inspection_id = fields.Many2one(
        'custom.quality.inspection',
        string='Inspection',
        required=True,
        ondelete='cascade',
    )

    inspection_field_id = fields.Many2one(
        'quality.point.inspection.field',
        string='Inspection Field',
        readonly=True,
    )

    template_id = fields.Many2one(
        'quality.inspection.template',
        string='Template',
        readonly=True,
    )

    product_category_id = fields.Many2one(
        'product.category',
        string='Product Category',
        readonly=True,
    )

    name = fields.Char(
        string='Inspection Field',
        readonly=True,
    )

    field_type = fields.Selection(
        [
            ('char', 'Text'),
            ('float', 'Number/Measurement'),
            ('integer', 'Integer'),
            ('selection', 'Selection'),
            ('boolean', 'Pass/Fail'),
            ('text', 'Long Text'),
            ('date', 'Date'),
        ],
        string='Field Type',
        readonly=True,
    )

    selection_options = fields.Char(
        string='Selection Options',
        readonly=True,
    )

    min_value = fields.Float(
        string='Minimum Value',
        readonly=True,
    )

    max_value = fields.Float(
        string='Maximum Value',
        readonly=True,
    )

    required = fields.Boolean(
        string='Required',
        readonly=True,
    )

    uom_id = fields.Many2one(
        'uom.uom',
        string='Unit of Measure',
        readonly=True,
    )

    # Values entered by the user
    value_char = fields.Char(
        string='Value',
    )

    value_text = fields.Text(
        string='Long Text Value',
    )

    value_float = fields.Float(
        string='Number Value',
    )

    value_integer = fields.Integer(
        string='Integer Value',
    )

    value_selection = fields.Char(
        string='Selection Value',
    )

    value_boolean = fields.Boolean(
        string='Pass / Fail',
    )

    value_date = fields.Date(
        string='Date Value',
    )

    @api.onchange('value_float')
    def _onchange_value_float(self):
        for line in self:
            if line.field_type != 'float':
                continue

            if line.min_value and line.value_float < line.min_value:
                return {
                    'warning': {
                        'title': _('Value Below Minimum'),
                        'message': _(
                            'The value for "%s" is below the minimum allowed value of %s.'
                        ) % (
                            line.name,
                            line.min_value,
                        ),
                    }
                }

            if line.max_value and line.value_float > line.max_value:
                return {
                    'warning': {
                        'title': _('Value Above Maximum'),
                        'message': _(
                            'The value for "%s" is above the maximum allowed value of %s.'
                        ) % (
                            line.name,
                            line.max_value,
                        ),
                    }
                }