# -*- encoding: utf-8 -*-
from odoo import api, fields, models, _

class Partner(models.Model):
	_inherit = 'res.partner'

	pe_driver_license = fields.Char("Licencia de conducir")
