from odoo import models


class QualityCheck(models.Model):
    _inherit = 'quality.check'

    def action_open_quality_check_wizard(self, current_check_id=None):

        check_ids = sorted(self.ids)

        check_id = self.browse(
            current_check_id or check_ids[0]
        )

        # -----------------------------------------
        # YOUR CUSTOM MULTI-FIELD INSPECTION
        # -----------------------------------------
        if check_id.point_id and check_id.point_id.is_multi_field:
            return check_id._action_open_multi_field_inspection()

        # -----------------------------------------
        # KEEP STANDARD ODOO BEHAVIOR
        # -----------------------------------------
        return super().action_open_quality_check_wizard(
            current_check_id
        )

    def _action_open_multi_field_inspection(self):
        self.ensure_one()

        # Find existing custom inspection
        inspection = self.env[
            'custom.quality.inspection'
        ].search(
            [
                ('quality_check_id', '=', self.id),
            ],
            limit=1,
        )

        # Create it if it doesn't exist
        if not inspection:
            inspection = self.env[
                'custom.quality.inspection'
            ].create(
                {
                    'quality_check_id': self.id,
                }
            )

        return {
            'type': 'ir.actions.act_window',
            'name': 'Quality Inspection',
            'res_model': 'custom.quality.inspection',
            'view_mode': 'form',
            'res_id': inspection.id,
            'target': 'new',
        }