# -*- coding: utf-8 -*-
from odoo import models, fields, api


class pe_sunat_server(models.Model):
	_name = 'cpe.server'
	_description = 'Servidores SUNAT'

	company_id = fields.Many2one(comodel_name='res.company', string='Compañía', required=True, default=lambda self:self.env.user.company_id)
	name = fields.Char("Nombre", required=True)
	url = fields.Char("Url", required=True)
	user = fields.Char("Usuario")
	password = fields.Char("Clave")
	description = fields.Text("Descripción")
	active = fields.Boolean("Activo", default=True)
	state = fields.Selection([
		('draft', 'Borrador'),
		('done', 'Listo'),
		('cancel', 'Anulado'),
	], string='Status', index=True, readonly=True, default='draft', copy=False)

	def action_draft(self):
		self.state = "draft"

	def action_done(self):
		self.state = "done"

	def action_cancel(self):
		self.state = "cancel"
