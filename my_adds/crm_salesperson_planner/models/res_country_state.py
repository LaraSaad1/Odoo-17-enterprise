from odoo import models, fields

class ResCountryState(models.Model):
    _inherit = 'res.country.state'

    code = fields.Char(required=False)
    country_id = fields.Many2one(
        comodel_name='res.country',
        default=lambda self: self.env['res.country'].search([('code', '=', 'EG')], limit=1),
    )