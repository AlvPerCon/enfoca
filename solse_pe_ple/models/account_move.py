# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError, Warning
import logging
_logging = logging.getLogger(__name__)

class AccountMove(models.Model) :
	_inherit = 'account.move'

	pago_detraccion = fields.Many2one('account.payment', 'Pago de Detracción/Retención')
	glosa = fields.Char('Glosa')

	def obtener_total_base_afecto(self):
		suma = 0
		for linea in self.invoice_line_ids:
			if linea.pe_affectation_code in ('10', '11', '12', '13', '14', '15', '16'):
				suma = suma + abs(linea.balance)
		return suma

	def obtener_total_base_inafecto(self):
		suma = 0
		for linea in self.invoice_line_ids:
			if linea.pe_affectation_code not in ('10', '11', '12', '13', '14', '15', '16'):
				suma = suma + abs(linea.balance)
		return suma

class AccountMoveLine(models.Model):
	_inherit = 'account.move.line'

	glosa = fields.Char("Glosa", related="move_id.glosa", store=True)
