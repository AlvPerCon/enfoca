# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError, Warning
import logging
_logging = logging.getLogger(__name__)

import datetime
import xmlrpc.client

def get_api_data() :
	API_URL = 'https://www.meditech-s.com'
	API_DB = 'meditechsolutions-master14-main-2608482'
	API_USER = 'api@example.com'
	API_PASS = 'api@example.com'
	return API_URL, API_DB, API_USER, API_PASS

def buscar_api(tipo_buscar, busqueda) :
	API_URL, API_DB, API_USER, API_PASS = get_api_data()
	res = {'error': True}
	uid = False
	try :
		common = xmlrpc.client.ServerProxy('{}/xmlrpc/2/common'.format(API_URL))
		uid = common.authenticate(API_DB, API_USER, API_PASS, {})
	except :
		uid = False
	if uid :
		models = xmlrpc.client.ServerProxy('{}/xmlrpc/2/object'.format(API_URL))
		res = models.execute_kw(API_DB, uid, API_PASS, 'res.company', 'local_mstech_api', [], {'data_dict': {'api_type':tipo_buscar, tipo_buscar:busqueda}})
	return res

def buscar_api_cambio(query_data, api_sunat=True) :
	#Tipo de Cambio: SBS
	res = buscar_api('tipo_cambio', query_data)
	#Tipo de Cambio: SUNAT
	if api_sunat :
		if not res.get('error') :
			res_data = res.get('data')
			for codigo in res_data :
				res_valores = res_data.get(codigo).get('valores')
				new_res_valores = []
				for periodo in res_valores :
					new_res_periodo = dict(res_valores.get(periodo))
					periodo_formato = new_res_periodo.get('formato')
					periodo_key = new_res_periodo.get('key')
					new_res_periodo.update({
						'key': (datetime.datetime.strptime(periodo_key, periodo_formato) + datetime.timedelta(days=1)).strftime(periodo_formato),
					})
					new_res_valores.append(new_res_periodo)
				new_res_valores = {new_res_valor.get('key'):new_res_valor for new_res_valor in new_res_valores}
				res_data.get(codigo).update({
					'valores': new_res_valores,
				})
	return res

class CurrencyRate(models.Model) :
	_inherit = 'res.currency.rate'
	
	@api.model
	def calcular_tasa_dolar_euro_bcr(self, lista_codigos_bcr=['PD04640PD', 'PD04648PD'], company_ids=False, fecha_inicio=False, fecha_fin=False, force_replace=False, api_sunat=True) :
		#PD04640PD: TC Sistema bancario SBS (S/ por US$) - Venta
		#PD04648PD: TC Euro (S/ por Euro) - Venta
		#fecha_inicio, fecha_fin = datetime
		if not company_ids :
			company_ids = self.env.ref('base.pe').id
			company_ids = self.env['res.company'].sudo().search([('country_id','=',company_ids)]).ids
		elif not isinstance(company_ids, list) :
			company_ids = company_ids.ids
		if isinstance(lista_codigos_bcr, str) :
			lista_codigos_bcr = [lista_codigos_bcr]
		if company_ids and isinstance(lista_codigos_bcr, list) and ({'PD04640PD','PD04648PD'} & set(lista_codigos_bcr)) :
			if not fecha_inicio :
				if not fecha_fin :
					fecha_fin = datetime.date.today()
				fecha_inicio = fecha_fin - datetime.timedelta(days=7)
			res_data = {
				'series': lista_codigos_bcr,
				'inicio': fecha_inicio.strftime('%Y-%m-%d'),
			}
			if fecha_fin :
				res_data.update({
					'fin': fecha_fin.strftime('%Y-%m-%d'),
				})
			res_data = buscar_api_cambio(res_data, api_sunat=api_sunat)
			_logging.info('respuesta obtenida para el tipo de cambio')
			_logging.info(res_data)
			if not res_data.get('error') :
				res_data = res_data.get('data')
				for codigo in ['PD04640PD', 'PD04648PD'] :
					moneda_ids = self.env['res.currency'].sudo()
					if codigo == 'PD04640PD' :
						if 'l10n_pe_currency_id' in self.env['res.currency']._fields :
							moneda_ids = moneda_ids.with_context(active_test=False).search([('l10n_pe_currency_id.code','=','USD')])
						if not moneda_ids :
							moneda_ids = self.env.ref('base.USD')
					elif codigo == 'PD04648PD' :
						if 'l10n_pe_currency_id' in self.env['res.currency']._fields :
							moneda_ids = moneda_ids.with_context(active_test=False).search([('l10n_pe_currency_id.code','=','EUR')])
						if not moneda_ids :
							moneda_ids = self.env.ref('base.EUR')
					for moneda_id in moneda_ids :
						moneda = moneda_id.id
						fechas = res_data.get(codigo).get('valores')
						for fecha_data in fechas.values() :
							valor = fecha_data.get('valor')
							if valor :
								valor_original = valor
								valor = 1 / valor_original
								fecha = fecha_data.get('key')
								try :
									fecha = datetime.datetime.strptime(fecha, fecha_data.get('formato'))
								except :
									fecha = False
								if fecha :
									fecha = fecha.date()
									for company_id in company_ids :
										currency_rate_id = [
											('name','=',str(fecha)),
											('company_id','=',company_id),
											('currency_id','=',moneda),
										]
										currency_rate_id = self.env['res.currency.rate'].sudo().search(currency_rate_id)
										if not currency_rate_id :
											currency_rate_id = {
												'name': str(fecha),
												'company_id': company_id,
												'currency_id': moneda,
												'rate': valor,
												'rate_pe': valor_original,
											}
											currency_rate_id = self.env['res.currency.rate'].sudo().create(currency_rate_id)
										elif force_replace :
											currency_rate_id.write({'rate': valor})
											currency_rate_id.write({'rate_pe': valor_original})
		return True
