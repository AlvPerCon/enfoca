# -*- coding: utf-8 -*-

from odoo import api, fields, tools, models, _
from odoo.exceptions import UserError, Warning
import logging
_logging = logging.getLogger(__name__)

class AccountMove(models.Model):
	_inherit = "account.move"

	telecredito_id = fields.Many2one('speru.telecredito', string='Telecrédito')