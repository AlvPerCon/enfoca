# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError, Warning
from .ple_report import get_last_day
from .ple_report import fill_name_data
from .ple_report import number_to_ascii_chr

import base64
import datetime
from io import StringIO, BytesIO
import pandas
import logging
_logging = logging.getLogger(__name__)

class PLEReport01(models.Model) :
	_name = 'ple.report.01'
	_description = 'PLE 01 - Estructura del Libro Caja y Bancos'
	_inherit = 'ple.report.templ'
	
	year = fields.Integer(required=True)
	month = fields.Selection(selection_add=[], required=True)
	
	line_ids = fields.Many2many(comodel_name='account.move.line', string='Movimientos', readonly=True)
	
	ple_txt_01 = fields.Text(string='Contenido del TXT 1.1')
	ple_txt_01_binary = fields.Binary(string='TXT 1.1')
	ple_txt_01_filename = fields.Char(string='Nombre del TXT 1.1')
	ple_xls_01_binary = fields.Binary(string='Excel 1.1')
	ple_xls_01_filename = fields.Char(string='Nombre del Excel 1.1')
	
	ple_txt_02 = fields.Text(string='Contenido del TXT 1.2')
	ple_txt_02_binary = fields.Binary(string='TXT 1.2', readonly=True)
	ple_txt_02_filename = fields.Char(string='Nombre del TXT 1.2')
	ple_xls_02_binary = fields.Binary(string='Excel 1.2', readonly=True)
	ple_xls_02_filename = fields.Char(string='Nombre del Excel 1.2')
	
	def get_default_filename(self, ple_id='010100', tiene_datos=False) :
		name = super().get_default_filename()
		name_dict = {
			'month': str(self.month).rjust(2,'0'),
			'ple_id': ple_id,
		}
		if not tiene_datos :
			name_dict.update({
				'contenido': '0',
			})
		fill_name_data(name_dict)
		name = name % name_dict
		return name
	
	def update_report(self) :
		res = super().update_report()
		start = datetime.date(self.year, int(self.month), 1)
		end = get_last_day(start)
		#current_offset = fields.Datetime.context_timestamp(self, fields.Datetime.now()).utcoffset()
		#start = start - current_offset
		#end = end - current_offset
		domain_company = []
		empresas = self.env['res.company'].sudo().search([])
		if len(empresas) > 1:
			domain_company = [('company_id','=',self.company_id.id), ('company_id.partner_id.country_id','=',pais_id)]
		pais_id = self.env.ref('base.pe').id
		lines = [
			('date','>=',str(start)),
			('date','<=',str(end)),
			('parent_state','=','posted'),
			('account_id.internal_type','=','liquidity'),
			('journal_id.type','in',['cash','bank']),
			('display_type','not in',['line_section','line_note']),
		]
		paremtros_buscar = domain_company + lines
		lines = self.env[self.line_ids._name].search(paremtros_buscar, order='date asc')
		self.line_ids = lines
		return res
	
	def generate_report(self) :
		res = super().generate_report()
		lines_to_write_01 = []
		lines_to_write_02 = []
		lines = self.line_ids.sudo()
		for move in lines :
			m = move.journal_id.type
			m_01 = []
			m_02 = []
			if m == 'cash' :
				m_01 = self.obtener_array_linea_efectivo(move)
			elif m == 'bank' :
				m_02 = self.obtener_array_linea_cuenta_corriente(move)
			if m_01 :
				try :
					lines_to_write_01.append('|'.join(m_01))
				except :
					raise UserError('Error: Datos no cumplen con los parámetros establecidos por SUNAT'+str(m_01))
			if m_02 :
				try :
					lines_to_write_02.append('|'.join(m_02))
				except :
					raise UserError('Error: Datos no cumplen con los parámetros establecidos por SUNAT'+str(m_02))
		name_01 = self.get_default_filename(ple_id='010100', tiene_datos=bool(lines_to_write_01))
		lines_to_write_01.append('')
		txt_string_01 = '\r\n'.join(lines_to_write_01)
		dict_to_write = dict()
		if txt_string_01 :
			headers = [
				'Periodo',
				'Código Único de la Operación (CUO)',
				'Número correlativo del asiento contable',
				'Código de la cuenta contable del efectivo',
				'Código de la Unidad de Operación, de la Unidad Económica Administrativa, de la Unidad de Negocio, de la Unidad de Producción, de la Línea, de la Concesión, del Local o del Lote',
				'Código del Centro de Costos, Centro de Utilidades o Centro de Inversión',
				'Tipo de Moneda de origen',
				'Tipo de Comprobante de Pago o Documento asociada a la operación',
				'Número serie del comprobante de pago o documento asociada a la operación',
				'Número del comprobante de pago o documento asociada a la operación',
				'Fecha contable',
				'Fecha de vencimiento',
				'Fecha de la operación o emisión',
				'Glosa o descripción de la naturaleza de la operación registrada',
				'Glosa referencial',
				'Movimientos del Debe',
				'Movimientos del Haber',
				'Código del libro, campo 1, campo 2 y campo 3 del Registro de Ventas e Ingresos o del Registro de Compras',
				'Indica el estado de la operación',
			]
			xlsx_file_base_64 = self._generate_xlsx_base64_bytes(txt_string_01, name_01[2:], headers=headers)
			dict_to_write.update({
				'ple_txt_01': txt_string_01,
				'ple_txt_01_binary': base64.b64encode(txt_string_01.encode()),
				'ple_txt_01_filename': name_01 + '.txt',
				'ple_xls_01_binary': xlsx_file_base_64.encode(),
				'ple_xls_01_filename': name_01 + '.xlsx',
			})
		else :
			dict_to_write.update({
				'ple_txt_01': False,
				'ple_txt_01_binary': False,
				'ple_txt_01_filename': False,
				'ple_xls_01_binary': False,
				'ple_xls_01_filename': False,
			})
		name_02 = self.get_default_filename(ple_id='010200', tiene_datos=bool(lines_to_write_02))
		lines_to_write_02.append('')
		txt_string_02 = '\r\n'.join(lines_to_write_02)
		if txt_string_02 :
			headers = [
				'Periodo',
				'Código Único de la Operación (CUO)',
				'Número correlativo del asiento contable',
				'Código de la entidad financiera donde se encuentra su cuenta bancaria',
				'Código de la cuenta bancaria del contribuyente',
				'Fecha de la operación',
				'Medio de pago utilizado en la operación bancaria',
				'Descripción de la operación bancaria.',
				'Tipo de Documento de Identidad del girador o beneficiario',
				'Número de Documento de Identidad del girador o beneficiario',
				'Apellidos y nombres, Denominación o Razón Social del girador o beneficiario. ',
				'Número de transacción bancaria, número de documento sustentatorio o número de control interno de la operación bancaria',
				'Parte deudora de saldos y movimientos',
				'Parte acreedora de saldos y movimientos',
				'Indica el estado de la operación',
			]
			xlsx_file_base_64 = self._generate_xlsx_base64_bytes(txt_string_02, name_02[2:], headers=headers)
			dict_to_write.update({
				'ple_txt_02': txt_string_02,
				'ple_txt_02_binary': base64.b64encode(txt_string_02.encode()),
				'ple_txt_02_filename': name_02 + '.txt',
				'ple_xls_02_binary': xlsx_file_base_64.encode(),
				'ple_xls_02_filename': name_02 + '.xlsx',
			})
		else :
			dict_to_write.update({
				'ple_txt_02': False,
				'ple_txt_02_binary': False,
				'ple_txt_02_filename': False,
				'ple_xls_02_binary': False,
				'ple_xls_02_filename': False,
			})
		dict_to_write.update({
			'date_generated': str(fields.Datetime.now()),
		})
		res = self.write(dict_to_write)
		return res

	def obtener_array_linea_efectivo(self, move):
		array_retorno = []
		try :
			move_line_data = move.read([
				'id',
				'name',
				'date',
				'debit',
				'credit',
			])[0]
			move_data = move.move_id.read([
				'id',
				'name',
			])[0]

			sunat_number = move_data.get('name')
			sunat_number = sunat_number and ('-' in sunat_number) and sunat_number.split('-') or ['','']
			move_name = move_line_data.get('name')
			if move_name :
				move_name = move_name.replace('\r', ' ').replace('\n', ' ').split()
				move_name = ' '.join(move_name)
			if not move_name :
				move_name = 'Movimiento'
			move_name = move_name[:200].strip()
			#V13
			#currency_name = move.always_set_currency_id.name
			currency_name = move.company_currency_id.name
			l10n_pe_document_type_code = move.move_id.pe_invoice_code or ''
			account_code = move.account_id.code or ''
			analytic_account_code = move.analytic_account_id.code or ''
			analytic_tag_codes = move.analytic_tag_ids.mapped('code')
			analytic_tags = ''
			while analytic_tag_codes and analytic_tag_codes[0] and (len('&'.join([analytic_tags, analytic_tag_codes[0]])) <= 24) :
				if analytic_tag_codes[0] :
					if analytic_tags :
						analytic_tags = '&'.join([analytic_tags, analytic_tag_codes[0]])
					else :
						analytic_tags = analytic_tag_codes[0]
				analytic_tag_codes = analytic_tag_codes[1:]
			#1-4
			array_retorno.extend([
				move_line_data.get('date').strftime('%Y%m00'),
				str(move_data.get('id')),
				'M' + str(move_line_data.get('id')).rjust(9,'0'),
				account_code.rstrip('0'),
			])
			#5-6
			array_retorno.extend([analytic_tags, analytic_account_code])
			#7
			array_retorno.append(currency_name)
			#8
			array_retorno.append(l10n_pe_document_type_code)
			#9-10
			array_retorno.extend(sunat_number)
			#11-12
			array_retorno.extend(['', ''])
			#13
			array_retorno.append(move_line_data.get('date').strftime('%d/%m/%Y'))
			#14-15
			array_retorno.extend([
				move_name,
				'',
			])
			#16-18
			array_retorno.extend([
				format(move_line_data.get('debit'), '.2f'),
				format(move_line_data.get('credit'), '.2f'),
				'',
			])
			#19-20
			array_retorno.extend(['1', ''])
		except Exception as e:
			_logging.info('error al obtener las lineas de tipo efectivo')
			_logging.info(e)
			
		return array_retorno

	def obtener_array_linea_cuenta_corriente(self, move):
		array_retorno = []
		try:
			move_line_data = move.read([
				'id',
				'name',
				'date',
				'debit',
				'credit',
			])[0]
			move_data = move.move_id.read([
				'id',
				'name',
			])[0]

			sunat_number = move_data.get('name')
			sunat_number = sunat_number and ('-' in sunat_number) and sunat_number.split('-') or ['','']
			move_name = move_line_data.get('name')
			if move_name :
				move_name = move_name.replace('\r', ' ').replace('\n', ' ').split()
				move_name = ' '.join(move_name)
			if not move_name :
				move_name = 'Movimiento'
			move_name = move_name[:200].strip()
			sunat_partner_code = move.move_id.partner_id.l10n_latam_identification_type_id.l10n_pe_vat_code or ''
			sunat_partner_vat = move.move_id.partner_id.vat or ''
			sunat_partner_name = move.move_id.partner_id.legal_name or move.move_id.partner_id.name or 'varios'
			payment = move.payment_id
			payment_backing = payment.ref or move.name
			payment_method_code = payment.l10n_pe_payment_method_code
			partner_bank = payment.partner_bank_id or (payment.journal_id or move.move_id.journal_id).bank_account_id
			bank_acc_number = partner_bank.acc_number
			bank_code = partner_bank.bank_id.l10n_pe_bank_code
			#1-3
			m_02.extend([
				move_line_data.get('date').strftime('%Y%m00'),
				str(move_data.get('id')),
				'M' + str(move_line_data.get('id')).rjust(9,'0'),
			])
			#4-5
			m_02.extend([
				bank_code,
				bank_acc_number,
			])
			#6-8
			m_02.extend([
				move_line_data.get('date').strftime('%d/%m/%Y'),
				payment_method_code or '',
				move_name or '',
			])
			#9-12
			m_02.extend([
				sunat_partner_code,
				sunat_partner_vat,
				sunat_partner_name,
				payment_backing,
			])
			#13-14
			m_02.extend([
				format(move_line_data.get('debit'), '.2f'),
				format(move_line_data.get('credit'), '.2f'),
			])
			#15-16
			m_02.extend([
				'1',
				'',
			])
		except Exception as e:
			_logging.info('error ')

		return array_retorno