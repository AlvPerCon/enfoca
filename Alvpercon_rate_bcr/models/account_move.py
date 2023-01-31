# -*- coding: utf-8 -*-

from odoo import api, fields, tools, models, _
from odoo.exceptions import UserError, Warning, ValidationError
import logging
_logging = logging.getLogger(__name__)

class AccountMoveLine(models.Model):
	_inherit = 'account.move.line'

	tipo_cambio = fields.Float('Tipo de cambio', compute="_compute_tipo_cambio" , digits=(12,3))
	debit_d = fields.Float('Débito Dolar', compute="_compute_debito_cambio" , digits=(12,3) )
	credit_d = fields.Float('Crédito Dolar', compute="_compute_credito_cambio" , digits=(12,3))
	date_related = fields.Date("Fecha relacionada", related="move_id.invoice_date")
	invoice_date = fields.Date("Fecha Factura", compute="_compute_invoice_date" , digits=(12,3))
	amount_currency_d = fields.Float('Importe en Dólares', compute="_compute_importe_d" , digits=(12,3) )
	date_acc_entry = fields.Date("Fecha Asiento", related="origin_move_line_id.invoice_date") # campo instalado desde solse_target_move
	es_x_apertrel = fields.Boolean("Movimiento por Apertura", related="move_id.es_x_apertura")
 
 
	def _compute_invoice_date(self):
	#def actualiza_fecha(self):	
	
		for reg in self:
			reg.invoice_date = reg.date_related
			if reg.invoice_date == False:
				if reg.date_acc_entry == False:
					reg.invoice_date = reg.date
				else:
					reg.invoice_date = reg.date_acc_entry
					

	#@api.depends('currency_id', 'date', 'company_id')
	#@api.depends('date', 'company_id')
	def _compute_tipo_cambio(self):
		for reg in self:
			#if not reg.date or not reg.currency_id or not reg.company_id:
			if not reg.invoice_date or not reg.currency_id or not reg.company_id:
			
				reg.tipo_cambio = 2
				continue
			currency_rate_id = [
				('name','=',str(reg.invoice_date)),
				('company_id','=',reg.company_id.id),
				('currency_id','=',2),
			]
			currency_rate_id = self.env['res.currency.rate'].sudo().search(currency_rate_id)
			#for regs in currency_rate_id:
			if currency_rate_id:
				if reg.journal_id.id == 4:
					reg.tipo_cambio = 0
				else:
					if reg.es_x_apertrel == False:
						reg.tipo_cambio = currency_rate_id.rate_pe
					else:
						reg.tipo_cambio = (reg.debit + reg.credit)/abs(reg.amount_currency)
			else:
				reg.tipo_cambio = 1
    
	def _compute_debito_cambio(self):
		for reg in self:
			if reg.currency_id.id == 2:
				if reg.amount_currency >=0:
					reg.debit_d = reg.amount_currency
				else:
					reg.debit_d = 0

			else:
				if reg.amount_currency >=0:
					if reg.es_x_apertrel == False:
						reg.debit_d = reg.amount_currency/reg.tipo_cambio
					else:
						reg.debit_d = reg.amount_currency
				else:
					reg.debit_d = 0
				
   
	def _compute_credito_cambio(self):
		for reg in self:
			if reg.currency_id.id == 2:
				if reg.amount_currency >=0:
					reg.credit_d = 0
				else:
					reg.credit_d = abs(reg.amount_currency)
    
			else:
				if reg.amount_currency >=0:
					reg.credit_d = 0
				else:
					if reg.es_x_apertrel == False:
						reg.credit_d = abs(reg.amount_currency/reg.tipo_cambio)
					else:
						reg.credit_d = abs(reg.amount_currency)
	
	def _compute_importe_d(self):
		for reg in self:
			reg.amount_currency_d = reg.debit_d - reg.credit_d
