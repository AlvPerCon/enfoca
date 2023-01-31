# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError, Warning

class Company(models.Model) :
	_inherit = 'res.company'
	
	def _generate_tasa_dolar_euro_bcr(self, country_code) :
		if country_code and (country_code.upper() == 'PE') :
			self.env['res.currency.rate'].sudo().calcular_tasa_dolar_euro_bcr(company_ids=self)
	
	@api.model
	def create(self, values) :
		res = super().create(values)
		res._generate_tasa_dolar_euro_bcr(res.country_id.code)
		return res
	
	def write(self, values) :
		res = super().write(values)
		if len(self) and values.get('country_id') :
			country_code = False
			try :
				country_code = self.env['res.country'].sudo().search_read([('id','=',values.get('country_id'))], ['code'])
			except :
				country_code = False
			if country_code :
				self._generate_tasa_dolar_euro_bcr(country_code[0].get('code'))
		return res
