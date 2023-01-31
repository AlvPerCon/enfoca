from odoo import models, fields

class AccountAccount(models.Model):
    _inherit = 'account.account'

    currency_multirate_affected = fields.Boolean(string='Execute Exchange Difference')
    multirate_currency_id = fields.Many2one('res.currency', string='Currency')

