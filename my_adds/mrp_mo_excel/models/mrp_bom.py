# models/mrp_bom.py
from odoo import api, fields, models
from odoo.tools import column_exists


class MrpBom(models.Model):
    _inherit = 'mrp.bom'

    component_ids = fields.Many2many(
        'product.product',
        'mrp_bom_component_rel', 'bom_id', 'product_id',
        string='Component',
        compute='_compute_component_ids',
        store=True,
    )

    component_qty = fields.Float(
        string='Component Quantity',
        compute='_compute_component_qty',
        store=True,
        default=0.0,
    )

    # ---------- computes (defensive) ----------
    @api.depends('bom_line_ids.product_id')
    def _compute_component_ids(self):
        for bom in self:
            products = bom.bom_line_ids.product_id
            bom.component_ids = [(6, 0, products.ids)]

    @api.depends('bom_line_ids.product_qty')
    def _compute_component_qty(self):
        for bom in self:
            bom.component_qty = sum(
                line.product_qty or 0.0 for line in bom.bom_line_ids
            )

    # ---------- safety net ----------
    @api.model
    def _component_qty_column_ready(self):
        return column_exists(self.env.cr, 'mrp_bom', 'component_qty')

    @api.model
    def read_group(self, domain, fields, groupby, offset=0, limit=None,
                   orderby=False, lazy=True):
        """Drop the component_qty measure if the column doesn't exist yet
        (module code deployed but not upgraded), instead of raising
        UndefinedColumn and breaking the whole pivot."""
        if not self._component_qty_column_ready():
            fields = [
                f for f in (fields or [])
                if f.split(':')[0] != 'component_qty'
            ]
        return super().read_group(
            domain, fields, groupby, offset=offset, limit=limit,
            orderby=orderby, lazy=lazy,
        )