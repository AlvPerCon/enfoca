# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError, Warning
import logging
_logging = logging.getLogger(__name__)

class Pertner(models.Model):
	_inherit = "res.partner"

	@api.model
	def default_get(self, default_fields):
		if 'default_property_account_payable_id' not in default_fields:
			return super().default_get(default_fields)
		default_property_account_payable_id = self._context.get('default_property_account_payable_id')
		contextual_self = self.with_context(default_property_account_payable_2_id=default_property_account_payable_id)
		return super(Pertner, contextual_self).default_get(default_fields)

	property_account_payable_2_id = fields.Many2one('account.account', company_dependent=True,
		string="Cuenta a pagar (Moneda Extranjera)",
		domain="[('internal_type', '=', 'payable'), ('deprecated', '=', False), ('company_id', '=', current_company_id)]",
		help="This account will be used instead of the default one as the payable account for the current partner",
		required=True)

	@api.onchange('property_account_payable_id')
	def _onchange_receivable_id(self):
		if self.property_account_payable_id and not self.property_account_payable_2_id:
			self.property_account_payable_2_id = self.property_account_payable_id.id

	@api.model
	def create(self, values) :
		res = super().create(values)
		if len(res) > 1:
			for reg in res:
				reg._onchange_receivable_id()
		else:
			res._onchange_receivable_id()
		return res