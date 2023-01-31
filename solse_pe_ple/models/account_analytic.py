# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError, Warning

class AccountAnalyticTag(models.Model) :
	_inherit = 'account.analytic.tag'
	
	code = fields.Char(string='Código')
