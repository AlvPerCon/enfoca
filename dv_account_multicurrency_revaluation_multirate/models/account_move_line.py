from odoo import models, fields, api


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'
    
    currency_name = fields.Char(related='currency_id.name', store=True)