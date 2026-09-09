# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError

# Exact name of the pricelist to use for the "سعر الوحدة" (unit price) column.
# Change this if the pricelist is renamed.
FARM_PRICELIST_NAME = 'قطاع مزارع'


class QuotationOfferWizard(models.TransientModel):
    _name = 'quotation.offer.wizard'
    _description = 'Quotation Offer (عرض سعر) Report Wizard'

    consignee_name = fields.Char(string='مرسل إليه', required=True)
    date_offer = fields.Date(string='تحريرا في', default=fields.Date.context_today)
    line_ids = fields.One2many(
        'quotation.offer.wizard.line', 'wizard_id', string='الأصناف',
    )

    def action_print_report(self):
        self.ensure_one()
        if not self.line_ids:
            raise UserError(_(
                "لا يوجد أصناف لطباعتها. الرجاء إغلاق هذه النافذة والتأكد من "
                "اختيار منتج واحد على الأقل قبل الضغط على زر الطباعة."
            ))
        return self.env.ref(
            'custom_quotation_offer.action_report_quotation_offer'
        ).report_action(self)


class QuotationOfferWizardLine(models.TransientModel):
    _name = 'quotation.offer.wizard.line'
    _description = 'Quotation Offer Wizard Line'
    _order = 'sequence, id'

    wizard_id = fields.Many2one(
        'quotation.offer.wizard', string='Wizard', ondelete='cascade', required=True,
    )
    sequence = fields.Integer(default=10)

    product_tmpl_id = fields.Many2one(
        'product.template', string='الصنف', required=True, ondelete='cascade',
    )
    # Pure read-only text for display in the wizard list - never a clickable
    # relational widget, so there's no way for it to open a nested popup.
    product_name = fields.Char(
        string='الصنف', related='product_tmpl_id.name', readonly=True,
    )

    # tech name = name (product.template.attribute.value) -> label = الوحدة
    # User picks the weight/unit variant value to print on the report.
    attribute_value_id = fields.Many2one(
        'product.template.attribute.value', string='الوحدة',
        domain="[('product_tmpl_id', '=', product_tmpl_id)]",
    )

    # tech name = price_unit, computed from the "قطاع مزارع" pricelist -> label = سعر الوحدة
    price_unit = fields.Float(
        string='سعر الوحدة', compute='_compute_price_unit', store=True, readonly=True,
    )

    @api.depends('product_tmpl_id', 'attribute_value_id')
    def _compute_price_unit(self):
        pricelist = self.env['product.pricelist'].search(
            [('name', '=', FARM_PRICELIST_NAME)], limit=1
        )
        for line in self:
            template = line.product_tmpl_id
            if not template:
                line.price_unit = 0.0
                continue

            # Resolve the actual variant (product.product) matching the chosen
            # unit/weight value, so the pricelist can apply variant-specific
            # price rules if any exist. Falls back to the template's default
            # variant if no match is found (e.g. single-variant products).
            variant = template.product_variant_id
            if line.attribute_value_id:
                matching = template.product_variant_ids.filtered(
                    lambda v: line.attribute_value_id in v.product_template_attribute_value_ids
                )
                if matching:
                    variant = matching[0]

            if not pricelist or not variant:
                line.price_unit = template.list_price
                continue

            try:
                price = pricelist._get_product_price(
                    variant, 1.0, uom=variant.uom_id, date=False,
                )
            except TypeError:
                # Signature fallback for slightly different core versions.
                price = pricelist._get_product_price(variant, 1.0)
            line.price_unit = price
