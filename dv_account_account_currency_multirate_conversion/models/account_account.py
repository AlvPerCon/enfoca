from odoo import models, fields

class AccountAccount(models.Model):
    _inherit = 'account.account'

    currency_multirate_conversion_affected = fields.Boolean(string='Execute Conversion Difference')
    multirate_conversion_currency_id = fields.Many2one('res.currency', string='Currency')

