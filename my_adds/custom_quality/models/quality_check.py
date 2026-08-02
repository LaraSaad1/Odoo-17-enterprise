from odoo import models
from odoo import api, fields


class QualityCheck(models.Model):
    _inherit = 'quality.check'

    point_id = fields.Many2one(
        "quality.point",
        string="Control Point",
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