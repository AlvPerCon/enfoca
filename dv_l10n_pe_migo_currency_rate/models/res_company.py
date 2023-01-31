from odoo import models, fields, api, _


class ResCompany(models.Model):
    _inherit = 'res.company'

    migo_token_api = fields.Char('Token Migo')
