# -*- coding: utf-8 -*-

from odoo import models, fields, api
import logging
_logging = logging.getLogger(__name__)


class AccountMove(models.Model):
	_inherit = 'account.move'

	asiento_det_ret = fields.Many2one('account.move', string='Asiento retención/detracción')

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

			datos_factura = {
				'journal_id': invoice_id.journal_id.id,
				'company_id': invoice_id.company_id.id,
				'move_type': 'in_invoice',
				'partner_id': self.contacto_asignado.id or contacto_defecto.id,
				"provision_id": self.id,
				'es_por_provision': True,
				'tipo_cuota': 'factura',
				'es_por_cuota': False,
				'invoice_line_ids': lineas_crear,
			}
			invoice_id.line_ids = lineas_crear

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
			invoice_id.line_ids = lineas_crear
