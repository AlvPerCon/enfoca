# -*- coding: utf-8 -*-

from odoo import api, fields, models
import logging
_logging = logging.getLogger(__name__)


class ResConfigSettings(models.TransientModel):
	_inherit = 'res.config.settings'

	cuenta_detracciones = fields.Many2one("account.account", string="Cuenta de detracciones", config_parameter='solse_pe_accountant.default_cuenta_detracciones')
	cuenta_retenciones = fields.Many2one("account.account", string="Cuenta de retenciones", config_parameter='solse_pe_accountant.default_cuenta_retenciones')

	"""def get_values(self):
		res = super(ResConfigSettings, self).get_values()
		_logging.info('datos de cuentas temporales::::::::::::::36')
		t_cuenta_detracciones = self.env['ir.config_parameter'].sudo().get_param('res.config.settings.cuenta_detracciones')
		t_cuenta_retenciones = self.env['ir.config_parameter'].sudo().get_param('res.config.settings.cuenta_retenciones')
		_logging.info(t_cuenta_detracciones)
		_logging.info(t_cuenta_retenciones)
		_logging.info('respuestaaaaaaaaa')
		_logging.info(res)
		res.update(
			cuenta_detracciones=t_cuenta_detracciones,
			cuenta_retenciones=t_cuenta_retenciones,
		)
		_logging.info('antes de devolver al final')
		_logging.info(res)
		return res
	"""


	"""def set_values(self):
		_logging.info('set valuessssssssssssssssssss')
		super(ResConfigSettings, self).set_values()
		_logging.info(self.cuenta_detracciones.id)
		_logging.info(self.cuenta_retenciones.id)
		self.env['ir.config_parameter'].sudo().set_param('res.config.settings.cuenta_detracciones', self.cuenta_detracciones.id)
		self.env['ir.config_parameter'].sudo().set_param('res.config.settings.cuenta_retenciones', self.cuenta_retenciones.id)
	"""
		