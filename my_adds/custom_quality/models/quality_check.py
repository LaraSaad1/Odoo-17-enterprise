from odoo import models
from odoo import api, fields
from odoo.exceptions import UserError



class QualityCheck(models.Model):
    _inherit = 'quality.check'

    inspection_history_ids = fields.Many2many(
        'custom.quality.inspection',
        string="Inspection History",
        compute='_compute_inspection_history_ids',
    )
 
    def _compute_inspection_history_ids(self):
        Inspection = self.env['custom.quality.inspection']
        for check in self:
            if not check.product_id:
                check.inspection_history_ids = Inspection
                continue
            check.inspection_history_ids = Inspection.search(
                [
                    ('product_id', '=', check.product_id.id),
                    ('state', '!=', 'draft'),
                ],
                order='create_date desc',
            )

    point_id = fields.Many2one(
        "quality.point",
        string="Control Point",
    )
    is_multi_field = fields.Boolean(
    related='point_id.is_multi_field',
    string='Is Multi-Field Inspection',
    )

    @api.onchange("product_id")
    def _onchange_product_id(self):
        for check in self:
            point = self.env["quality.point"].search([
                ("product_ids", "in", check.product_id.id),
            ], limit=1)

            check.point_id = point

    def action_open_quality_check_wizard(self, current_check_id=None):
        """
        This is the existing Odoo Quality Check button.

        We only change its behavior when the Quality Check
        has a Control Point configured for Multi-Field Inspection.

        Otherwise, standard Odoo behavior is preserved.
        """

        check_ids = sorted(self.ids)

        check_id = self.browse(
            current_check_id or check_ids[0]
        )

        # -----------------------------------------
        # CUSTOM MULTI-FIELD FLOW
        # -----------------------------------------
        if (
            check_id.point_id
            and check_id.point_id.is_multi_field
        ):
            return check_id.action_open_multi_field_inspection()

        # -----------------------------------------
        # STANDARD ODOO FLOW
        # -----------------------------------------
        return super().action_open_quality_check_wizard(
            current_check_id
        )

    def action_print_inspection_report(self):
        
        self.ensure_one()
 
        inspection = self.env[
            'custom.quality.inspection'
        ].search(
            [
                ('quality_check_id', '=', self.id),
            ],
            limit=1,
        )
 
        if not inspection:
            raise UserError(
                _(
                    'No Custom Inspection was found for this '
                    'Quality Check yet. Please fill in the '
                    'inspection first.'
                )
            )
 
        return self.env.ref(
            'custom_quality.action_report_custom_quality_inspection'
        ).report_action(inspection)

    def action_open_multi_field_inspection(self):
        """
        Open the Custom Quality Inspection.

        """

        self.ensure_one()

        # -----------------------------------------
        # FIND EXISTING CUSTOM INSPECTION
        # -----------------------------------------
        inspection = self.env[
            'custom.quality.inspection'
        ].search(
            [
                ('quality_check_id', '=', self.id),
            ],
            limit=1,
        )

        # -----------------------------------------
        # CREATE CUSTOM INSPECTION IF NOT FOUND
        # -----------------------------------------
        if not inspection:
            inspection = self.env[
                'custom.quality.inspection'
            ].create(
                {
                    'quality_check_id': self.id,
                }
            )

        # -----------------------------------------
        # OPEN CUSTOM INSPECTION
        # -----------------------------------------
        return {
            'type': 'ir.actions.act_window',
            'name': 'Quality Inspection',
            'res_model': 'custom.quality.inspection',
            'view_mode': 'form',
            'res_id': inspection.id,
            'target': 'new',
        }