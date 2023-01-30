from odoo import models, fields, _
from odoo.exceptions import UserError
import logging
_logging = logging.getLogger(__name__)

class ValidateAccountMove(models.TransientModel):
	_name = "speru.telecredito.crear"
	_description = "Crear reporte para Telecredito"

	diario_pago = fields.Many2one('account.journal', 'Diario de pago', domain=[('type', 'in', ['bank'])])
	name = fields.Char('Nombre de lote')
	
	def asignar_pagos(self):
		facturas = self.env['account.move'].browse(self._context.get('active_ids', []))
		telecredito = self.env['speru.telecredito'].search([('state', '=', 'borrador')])
		if not telecredito:
			telecredito = self.env['speru.telecredito'].create({
				'name': self.name,
				'cuenta_cargo': self.diario_pago.id,
			})
		else:
			telecredito.write({
				'name': self.name,
				'cuenta_cargo': self.diario_pago.id,
			})
		for factura in facturas:
			if not factura.telecredito_id:
				factura.write({
					'telecredito_id': telecredito.id,
				})

		action = self.env["ir.actions.actions"]._for_xml_id("solse_pe_telecredito.action_telecredito_form")
		form_view = [(self.env.ref('solse_pe_telecredito.view_telecredito_form').id, 'form')]
		if 'views' in action:
			action['views'] = form_view + [(state,view) for state,view in action['views'] if view != 'form']
		else:
			action['views'] = form_view
		action['res_id'] = telecredito.id
		action['context'] = {}
		return action
		


"""
solse_pe_telecredito.wizard.pago_telecredito: pagossssssssssss 
2022-01-21 20:54:23,567 7933 INFO demo14n1 odoo.addons.solse_pe_telecredito.wizard.pago_telecredito: account.payment(3, 2, 1) 
2022-01-21 20:54:23,568 7933 INFO demo14n1 werkzeug: 127.0.0.1 - - [21/Jan/2022 20:54:23] "POST /web/dataset/call_button HTTP

"""