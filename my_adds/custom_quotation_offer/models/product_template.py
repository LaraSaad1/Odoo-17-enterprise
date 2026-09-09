# -*- coding: utf-8 -*-
from odoo import models


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    def action_open_quotation_offer_wizard(self):
        """Open the "عرض سعر" print wizard, pre-filled with:
        - this product, when called from the Product form view (self = 1 record).
        - the ticked products, when called from the Product list/tree view
          (self = the selected records).

        Nothing is picked manually by the user - the wizard's line_ids are
        built here, server-side, and handed to the wizard via the standard
        'default_line_ids' context mechanism, so there is no dependency on
        active_id/active_model guessing and no risk of an empty, clickable
        Many2one cell opening a nested "create record" popup.
        """
        line_commands = []
        for product in self:
            # Pre-select the product's own variant's attribute value when it
            # only has one variant (nothing to guess); otherwise left blank
            # for the user to pick in the wizard.
            ptav = self.env['product.template.attribute.value']
            variant_ptavs = product.product_variant_id.product_template_attribute_value_ids
            if len(product.product_variant_ids) == 1 and variant_ptavs:
                ptav = variant_ptavs[:1]
            line_commands.append((0, 0, {
                'product_tmpl_id': product.id,
                'attribute_value_id': ptav.id if ptav else False,
            }))

        return {
            'type': 'ir.actions.act_window',
            'name': 'طباعة عرض سعر',
            'res_model': 'quotation.offer.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_line_ids': line_commands},
        }
