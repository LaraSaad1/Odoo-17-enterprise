# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class TelesalesCall(models.Model):
    _name = 'telesales.call'
    _description = 'Telesales Call'
    _order = 'call_date desc, id desc'
    _rec_name = 'customer_id'
    _inherit = ['mail.thread', 'mail.activity.mixin']


    name = fields.Char(
        string='المرجع', copy=False, readonly=True,
        default=lambda self: _('New'))

    call_date = fields.Date(
        string='التاريخ', required=True, default=fields.Date.context_today,
        tracking=True)

    day_of_week = fields.Selection(
        [('0', 'الاثنين'), ('1', 'الثلاثاء'), ('2', 'الأربعاء'),
         ('3', 'الخميس'), ('4', 'الجمعة'), ('5', 'السبت'),
         ('6', 'الأحد')],
        string='اليوم', default=lambda self: str(fields.Date.context_today(self).weekday()))

    customer_id = fields.Many2one(
        'telesales.customer', string='اسم العميل', tracking=True)
    phone = fields.Char(string='التليفون')
    notes = fields.Text(string='ملاحظات')

    governorate_id = fields.Many2one(
        'res.country.state', string='المحافظة',
        domain="[('country_id.code', '=', 'EG')]")
    district = fields.Char(string='المركز')

    category = fields.Selection(
        [('farmer', 'مزارع'),
         ('commercial', 'تجاري'),
         ('car', 'عربيات')],
        string='التصنيف', tracking=True)

    product_id = fields.Many2one('product.product', string='اسم المنتج')
    employee_id = fields.Many2one(
        'res.users', string='اسم الموظف',
        default=lambda self: self.env.user, tracking=True)
    employee_notes = fields.Text(string='ملاحظات الموظف')

    status = fields.Selection(
        [('draft', 'Draft'),
         ('confirmed', 'Confirmed'),
         ('cancelled', 'Cancelled')],
        string='Status', default='draft', tracking=True, copy=False)

    company_id = fields.Many2one(
        'res.company', string='الشركة',
        default=lambda self: self.env.company)

    @api.onchange('call_date')
    def _onchange_call_date(self):
        for rec in self:
            if rec.call_date:
                rec.day_of_week = str(rec.call_date.weekday())

    @api.onchange('customer_id')
    def _onchange_customer_id(self):
        for rec in self:
            if rec.customer_id:
                rec.phone = rec.customer_id.phone
                rec.governorate_id = rec.customer_id.governorate_id
                rec.district = rec.customer_id.district
                rec.category = rec.customer_id.category

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('telesales.call') or _('New')
        return super().create(vals_list)

    def action_confirm(self):
        self.write({'status': 'confirmed'})

    def action_cancel(self):
        self.write({'status': 'cancelled'})

    def action_reset_to_draft(self):
        self.write({'status': 'draft'})
