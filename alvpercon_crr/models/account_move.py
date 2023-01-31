# -*- coding: utf-8 -*-

from odoo import models, fields, api


class AccountMove(models.Model):
	_inherit = 'account.move'    
	
	ruc_cc = fields.Char(string='Ruc', related="partner_id.vat")
		

	