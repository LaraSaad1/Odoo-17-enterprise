from odoo import models


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    def _create_check(self, point, current_move):
        if not point.is_multi_field:
            return super()._create_check(point, current_move)
        
        # Create ONE check with all fields
        check_vals = {
            'point_id': point.id,
            'team_id': point.team_id.id,
            'company_id': point.company_id.id,
            'picking_id': self.id,
            'product_id': current_move.product_id.id,
            'test_type_id': point.test_type_id.id,
            'title': point.title or point.name,
        }
        return self.env['quality.check'].create(check_vals)