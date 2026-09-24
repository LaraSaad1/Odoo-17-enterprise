# -*- coding: utf-8 -*-
from odoo import fields, models


class TelesalesCustomer(models.Model):
    _name = 'telesales.customer'
    _description = 'Telesales Customer'
    _order = 'name'
    _rec_name = 'name'

    name = fields.Char(string='اسم العميل')
    phone = fields.Char(string='التليفون')
    governorate_id = fields.Many2one(
        'res.country.state', string='المحافظة',
        domain="[('country_id.code', '=', 'EG')]")
    district = fields.Char(string='المركز')
    category = fields.Selection(
        [('farmer', 'مزارع'),
         ('commercial', 'تجاري'),
         ('car', 'عربيات')],
        string='التصنيف')
    notes = fields.Text(string='ملاحظات')
    active = fields.Boolean(default=True)
