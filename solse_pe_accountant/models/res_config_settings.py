# -*- coding: utf-8 -*-

from odoo import api, fields, models
import logging
_logging = logging.getLogger(__name__)


class ResConfigSettings(models.TransientModel):
	_inherit = 'res.config.settings'

	cuenta_detracciones = fields.Many2one("account.account", string="Cuenta de detracciones", config_parameter='solse_pe_accountant.default_cuenta_detracciones')
	cuenta_retenciones = fields.Many2one("account.account", string="Cuenta de retenciones", config_parameter='solse_pe_accountant.default_cuenta_retenciones')
