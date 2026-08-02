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

                vals['name'] = (
                    self.env[
                        'ir.sequence'
                    ].next_by_code(
                        'custom.quality.inspection'
                    )
                    or _('New')
                )

        inspections = super().create(vals_list)

        for inspection in inspections:
            inspection._load_inspection_fields()

        return inspections

    def _load_inspection_fields(self):

        self.ensure_one()

        point = self.quality_point_id

        if not point:
            raise UserError(
                _(
                    'The Quality Check is not linked to '
                    'a Quality Control Point.'
                )
            )

        if not point.is_multi_field:
            raise UserError(
                _(
                    'This Quality Control Point is not configured '
                    'for Multi-Field Inspection.'
                )
            )

        if not point.inspection_field_ids:
            raise UserError(
                _(
                    'The Quality Control Point "%s" has no '
                    'inspection fields configured.'
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
                        'template_field_id': (
                            field.template_field_id.id
                        ),
                        'name': field.name,
                        'test_type_id': field.test_type_id.id,
                        'required': field.required,
                        'help_text': field.help_text,
                        'sequence': field.sequence,
                    },
                )
            )

        self.inspection_line_ids = lines

    def action_pass(self):

        for inspection in self:

            inspection._validate_required_fields()

            inspection.state = 'pass'

            if inspection.quality_check_id:
                inspection.quality_check_id.do_pass()

        return {
            'type': 'ir.actions.act_window_close'
        }

    def action_fail(self):

        for inspection in self:

            inspection._validate_required_fields()

            inspection.state = 'fail'

            if inspection.quality_check_id:
                inspection.quality_check_id.do_fail()

        return {
            'type': 'ir.actions.act_window_close'
        }

    def _validate_required_fields(self):

        self.ensure_one()

        for line in self.inspection_line_ids:

            if not line.required:
                continue

            if not line._has_value():
                raise ValidationError(
                    _(
                        'The field "%s" is required.'
                    ) % line.name
                )


class QualityInspectionLine(models.Model):
    _name = 'custom.quality.inspection.line'
    _description = 'Custom Quality Inspection Line'
    _order = 'sequence, id'

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
        string='Inspection Form',
        readonly=True,
    )

    template_field_id = fields.Many2one(
        'quality.inspection.template.field',
        string='Template Field',
        readonly=True,
    )

    name = fields.Char(
        string='Inspection Name',
        readonly=True,
    )

    test_type_id = fields.Many2one(
        'quality.point.test_type',
        string='Test Type',
    )

    test_type = fields.Char(
        related='test_type_id.technical_name',
        string='Test Type Code',
        store=True,
        readonly=True,
    )

    required = fields.Boolean(
        string='Required',
        readonly=True,
    )

    help_text = fields.Char(
        string='Help Text',
        readonly=True,
    )

    sequence = fields.Integer(
        string='Sequence',
        readonly=True,
    )

    # OLD generic field — kept for backward compatibility if referenced elsewhere
    value = fields.Char(
        string='Result',
    )

    # NEW typed fields
    value_text = fields.Char(string='Result')
    value_number = fields.Float(string='Measured Value')
    value_passfail = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
    ], string='Result')
    value_picture = fields.Binary(string='Picture', attachment=True)
    value_picture_filename = fields.Char(string='File Name')

    def _has_value(self):
        self.ensure_one()
        if self.test_type == 'picture':
            return bool(self.value_picture)
        if self.test_type == 'measure':
            return bool(self.value_number)
        if self.test_type == 'passfail':
            return bool(self.value_passfail)
        return bool(self.value_text)