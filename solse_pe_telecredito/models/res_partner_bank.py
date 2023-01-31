# -*- coding: utf-8 -*-

from odoo import api, fields, tools, models, _
from odoo.exceptions import UserError, Warning
import base64
import logging
_logging = logging.getLogger(__name__)


class ResPartnerBank(models.Model):
	_inherit = 'res.partner.bank'

	tipo_cuenta = fields.Selection([('C', 'Corriente'), ('M', 'Maestra'), ('A', 'Ahorros'), ('B', 'Interbancaria'), ('D', 'Detracción'), ('E', 'Exterior')], default="C", string="Tipo de cuenta")