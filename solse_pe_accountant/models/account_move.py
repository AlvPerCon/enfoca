# -*- coding: utf-8 -*-

from odoo import models, fields, api
import logging
_logging = logging.getLogger(__name__)

class AccountPayment(models.Model):
	_inherit = 'account.payment'

	transaction_number = fields.Char(string='Número de operación')

class AccountMoveLine(models.Model):
	_inherit = 'account.move.line'

	transaction_number = fields.Char(related='payment_id.transaction_number', store=True)

class StatementLine(models.Model):
	_inherit = 'account.bank.statement.line'

	transaction_number = fields.Char(string='Número de transacción')


class AccountMove(models.Model):
	_inherit = 'account.move'

	transaction_number = fields.Char(related='payment_id.transaction_number', store=True)
	asiento_det_ret = fields.Many2one('account.move', string='Asiento retención/detracción')
	pago_detraccion = fields.Many2one('account.payment', 'Pago de Detracción/Retención')

	es_x_apertura = fields.Boolean("Movimiento por Apertura")
	fecha_apertura = fields.Date("Fecha Apertura", default=fields.Date.context_today, readonly=True, states={'draft': [('readonly', False)]},)

	@api.onchange('es_x_apertura', 'fecha_apertura')
	def _onchange_fecha_apertura(self):
		if self.es_x_apertura and self.fecha_apertura:
			self.date = self.fecha_apertura or fields.Date.context_today(self)
		else:
			self.date = self.invoice_date or fields.Date.context_today(self)

	def _post(self, soft=True):
		res = super(AccountMove, self)._post()

		return res

	def agregar_movimiento_retencion(self):
		invoice_id = self
		if invoice_id.tiene_retencion:
			cuenta_ret_id = self.env['ir.config_parameter'].sudo().get_param('solse_pe_accountant.default_cuenta_retenciones')
			cuenta_ret_id = int(cuenta_ret_id)
			debit = False
			credit = False
			linea_temp = False
			lineas_crear = []
			suma_afectar = 0
			cuenta_id = False
			for linea in invoice_id.line_ids:
				if invoice_id.move_type == 'in_invoice':
					if linea.account_id.internal_type == "payable" and linea.debit == 0:
						suma_afectar = suma_afectar + linea.credit
						cuenta_id = linea.account_id.id
				elif invoice_id.move_type == 'out_invoice':
					if linea.account_id.internal_type == "receivable" and linea.credit == 0:
						suma_afectar = suma_afectar + linea.debit
						cuenta_id = linea.account_id.id

			if invoice_id.move_type == 'in_invoice':
				lineas_crear.append((0, 0, {
					'currency_id': invoice_id.currency_id.id,
					'account_id': cuenta_id,
					'exclude_from_invoice_tab': True,
					'debit': invoice_id.monto_retencion,
					'credit': 0.0,
					'amount_currency': invoice_id.monto_retencion_base,
				}))
				lineas_crear.append((0, 0, {
					'currency_id': invoice_id.currency_id.id,
					'account_id': cuenta_ret_id,
					'exclude_from_invoice_tab': True,
					'debit': 0.0,
					'credit': invoice_id.monto_retencion,
					'amount_currency': invoice_id.monto_retencion_base * -1,
				}))
			elif invoice_id.move_type == 'out_invoice':
				lineas_crear.append((0, 0, {
					'currency_id': invoice_id.currency_id.id,
					'account_id': cuenta_id,
					'debit': 0.00,
					'credit': invoice_id.monto_retencion,
					'amount_currency': invoice_id.monto_retencion_base,
					'exclude_from_invoice_tab': True,
				}))
				lineas_crear.append((0, 0, {
					'currency_id': invoice_id.currency_id.id,
					'account_id': cuenta_ret_id,
					'debit': invoice_id.monto_retencion,
					'credit': 0.00,
					'amount_currency': invoice_id.monto_retencion_base * -1,
					'exclude_from_invoice_tab': True,
				}))

			diario_aplicar = self.env["account.journal"].search([("type", "=", "general")], limit=1)
			paramtros_retencion = {
				"move_type": "entry",
				"journal_id": diario_aplicar.id,
				"line_ids": lineas_crear,
			}
			factura_retencion = self.env['account.move'].create(paramtros_retencion)
			factura_retencion.action_post()
			invoice_id.asiento_det_ret = factura_retencion.id

	def agregar_movimiento_detraccion(self):
		invoice_id = self
		if invoice_id.tiene_detraccion:
			cuenta_det_id = self.env['ir.config_parameter'].sudo().get_param('solse_pe_accountant.default_cuenta_detracciones')
			cuenta_det_id = int(cuenta_det_id)
			debit = False
			credit = False
			linea_temp = False
			lineas_crear = []
			suma_afectar = 0
			cuenta_id = False
			for linea in invoice_id.line_ids:
				if invoice_id.move_type == 'in_invoice':
					if linea.account_id.internal_type == "payable" and linea.debit == 0:
						suma_afectar = suma_afectar + linea.credit
						cuenta_id = linea.account_id.id
				elif invoice_id.move_type == 'out_invoice':
					if linea.account_id.internal_type == "receivable" and linea.credit == 0:
						suma_afectar = suma_afectar + linea.debit
						cuenta_id = linea.account_id.id

			if invoice_id.move_type == 'in_invoice':
				lineas_crear.append((0, 0, {
					'currency_id': invoice_id.currency_id.id,
					'account_id': cuenta_id,
					'debit': invoice_id.monto_detraccion,
					'credit': 0.0,
					'amount_currency': invoice_id.monto_detraccion_base,
					'exclude_from_invoice_tab': True,
				}))
				lineas_crear.append((0, 0, {
					'currency_id': invoice_id.currency_id.id,
					'account_id': cuenta_det_id,
					'debit': 0.0,
					'credit': invoice_id.monto_detraccion,
					'amount_currency': invoice_id.monto_detraccion_base * -1,
					'exclude_from_invoice_tab': True,
				}))
			elif invoice_id.move_type == 'out_invoice':
				lineas_crear.append((0, 0, {
					'currency_id': invoice_id.currency_id.id,
					'account_id': cuenta_id,
					'debit': 0.00,
					'credit': invoice_id.monto_detraccion,
					'amount_currency': invoice_id.monto_detraccion_base,
					'exclude_from_invoice_tab': True,
				}))
				lineas_crear.append((0, 0, {
					'currency_id': invoice_id.currency_id.id,
					'account_id': cuenta_det_id,
					'debit': invoice_id.monto_detraccion,
					'credit': 0.00,
					'amount_currency': invoice_id.monto_detraccion_base * -1,
					'exclude_from_invoice_tab': True,
				}))

			diario_aplicar = self.env["account.journal"].search([("type", "=", "general")], limit=1)
			paramtros_detraccion = {
				"move_type": "entry",
				"journal_id": diario_aplicar.id,
				"line_ids": lineas_crear,
			}
			factura_detraccion = self.env['account.move'].create(paramtros_detraccion)
			factura_detraccion.action_post()
			invoice_id.asiento_det_ret = factura_detraccion.id
			#invoice_id.line_ids = lineas_crear
