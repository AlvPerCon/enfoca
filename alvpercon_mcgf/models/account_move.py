# -*- coding: utf-8 -*-

from odoo import api, fields, tools, models, _
from odoo.exceptions import UserError, Warning, ValidationError
import logging
_logging = logging.getLogger(__name__)

class AccountMove(models.Model):
	_inherit = 'account.move'
 
	glosa = fields.Char('Glosa')

class AccountMoveLine(models.Model):
	_inherit = 'account.move.line'

	glosa = fields.Char("Glosa", related="move_id.glosa")
	
 
 