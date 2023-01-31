# -*- coding: utf-8 -*-

from odoo import models, fields, api


class AccountMove(models.Model):
	_inherit = 'account.move'

	caja_chicaxp = fields.Boolean('Caja Chica')
		
