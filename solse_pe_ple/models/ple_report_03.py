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

class PLEReport03(models.Model) :
	_name = 'ple.report.03'
	_description = 'PLE 03 - Estructura del Libro Inventarios y Balances'
	_inherit = 'ple.report.templ'
	
	year = fields.Integer(required=True)
	month = fields.Selection(selection_add=[], required=True)
	day = fields.Integer(required=True)
	
	line_ids = fields.Many2many(comodel_name='account.move.line', string='Movimientos', readonly=True)
	
	ple_txt_01 = fields.Text(string='Contenido del TXT 3.1')
	ple_txt_01_binary = fields.Binary(string='TXT 3.1')
	ple_txt_01_filename = fields.Char(string='Nombre del TXT 3.1')
	ple_xls_01_binary = fields.Binary(string='Excel 3.1')
	ple_xls_01_filename = fields.Char(string='Nombre del Excel 3.1')
	ple_txt_02 = fields.Text(string='Contenido del TXT 3.2')
	ple_txt_02_binary = fields.Binary(string='TXT 3.2', readonly=True)
	ple_txt_02_filename = fields.Char(string='Nombre del TXT 3.2')
	ple_xls_02_binary = fields.Binary(string='Excel 3.2', readonly=True)
	ple_xls_02_filename = fields.Char(string='Nombre del Excel 3.2')
	ple_txt_03 = fields.Text(string='Contenido del TXT 3.3')
	ple_txt_03_binary = fields.Binary(string='TXT 3.3', readonly=True)
	ple_txt_03_filename = fields.Char(string='Nombre del TXT 3.3')
	ple_xls_03_binary = fields.Binary(string='Excel 3.3', readonly=True)
	ple_xls_03_filename = fields.Char(string='Nombre del Excel 3.3')
	ple_txt_04 = fields.Text(string='Contenido del TXT 3.4')
	ple_txt_04_binary = fields.Binary(string='TXT 3.4', readonly=True)
	ple_txt_04_filename = fields.Char(string='Nombre del TXT 3.4')
	ple_xls_04_binary = fields.Binary(string='Excel 3.4', readonly=True)
	ple_xls_04_filename = fields.Char(string='Nombre del Excel 3.4')
	ple_txt_05 = fields.Text(string='Contenido del TXT 3.5')
	ple_txt_05_binary = fields.Binary(string='TXT 3.5', readonly=True)
	ple_txt_05_filename = fields.Char(string='Nombre del TXT 3.5')
	ple_xls_05_binary = fields.Binary(string='Excel 3.5', readonly=True)
	ple_xls_05_filename = fields.Char(string='Nombre del Excel 3.5')
	ple_txt_06 = fields.Text(string='Contenido del TXT 3.6')
	ple_txt_06_binary = fields.Binary(string='TXT 3.6', readonly=True)
	ple_txt_06_filename = fields.Char(string='Nombre del TXT 3.6')
	ple_xls_06_binary = fields.Binary(string='Excel 3.6', readonly=True)
	ple_xls_06_filename = fields.Char(string='Nombre del Excel 3.6')
	ple_txt_11 = fields.Text(string='Contenido del TXT 3.11')
	ple_txt_11_binary = fields.Binary(string='TXT 3.11', readonly=True)
	ple_txt_11_filename = fields.Char(string='Nombre del TXT 3.11')
	ple_xls_11_binary = fields.Binary(string='Excel 3.11', readonly=True)
	ple_xls_11_filename = fields.Char(string='Nombre del Excel 3.11')
	ple_txt_12 = fields.Text(string='Contenido del TXT 3.12')
	ple_txt_12_binary = fields.Binary(string='TXT 3.12', readonly=True)
	ple_txt_12_filename = fields.Char(string='Nombre del TXT 3.12')
	ple_xls_12_binary = fields.Binary(string='Excel 3.12', readonly=True)
	ple_xls_12_filename = fields.Char(string='Nombre del Excel 3.12')
	ple_txt_13 = fields.Text(string='Contenido del TXT 3.13')
	ple_txt_13_binary = fields.Binary(string='TXT 3.13', readonly=True)
	ple_txt_13_filename = fields.Char(string='Nombre del TXT 3.13')
	ple_xls_13_binary = fields.Binary(string='Excel 3.13', readonly=True)
	ple_xls_13_filename = fields.Char(string='Nombre del Excel 3.13')
	ple_txt_14 = fields.Text(string='Contenido del TXT 3.14')
	ple_txt_14_binary = fields.Binary(string='TXT 3.14', readonly=True)
	ple_txt_14_filename = fields.Char(string='Nombre del TXT 3.14')
	ple_xls_14_binary = fields.Binary(string='Excel 3.14', readonly=True)
	ple_xls_14_filename = fields.Char(string='Nombre del Excel 3.14')
	
	def get_default_filename(self, ple_id='030100', tiene_datos=False, report_03='07') :
		name = super().get_default_filename()
		name_dict = {
			'month': str(self.month).rjust(2,'0'),
			'day': str(self.day).rjust(2,'0'),
			'ple_id': ple_id,
			'report_03': report_03,
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
		start = datetime.date(self.year, int(self.month), self.day)
		end = start
		lines = self.env.ref('base.pe').id
		lines = [
			('company_id','=',self.company_id.id),
			('company_id.partner_id.country_id','=',lines),
			('move_id.state','=','posted'),
			('date','>=',str(start)),
			('date','<=',str(end)),
		]
		lines = self.env[self.line_ids._name].search(lines, order='date asc')
		self.line_ids = lines
		return res
	
	def generate_report(self) :
		res = super().generate_report()
		lines_to_write_01 = []
		lines_to_write_02 = []
		lines_to_write_03 = []
		lines_to_write_04 = []
		lines_to_write_05 = []
		lines_to_write_06 = []
		lines_to_write_11 = []
		lines_to_write_12 = []
		lines_to_write_13 = []
		lines_to_write_14 = []
		lines = self.line_ids.sudo()
		for move in lines :
			m = move.account_id.group_id.code_prefix_start
			m_01 = []
			m_02 = []
			m_03 = []
			m_04 = []
			m_05 = []
			m_06 = []
			m_11 = []
			m_12 = []
			m_13 = []
			m_14 = []
			if m in ['10'] :
				try :
					date = move.date
					#1-2
					m_02.extend([
						date.strftime('%Y%m%d'),
						move.account_id.code.rstrip('0'),
					])
					#V13
					#bank_account_id = move.payment_id.partner_bank_account_id
					bank_account_id = move.payment_id.partner_bank_id
					bank_id = bank_account_id.bank_id
					bank_code = '99'
					if bank_id and (move.journal_id.type != 'cash') :
						#bank_code = bank_id.   .code or bank_code
						bank_code = '34'
					#3-5
					m_02.extend([
						bank_code,
						(bank_code!='99') and bank_account_id.acc_number or '-',
						'PEN', #move.company_currency_id.name,
					])
					#6-9
					m_02.extend([
						format(move.debit, '.2f'),
						format(move.credit, '.2f'),
						'1',
						'',
					])
				except :
					_logging.info('error en lineaaaaaaaaaaaaaa 650')
					m_02 = []
			elif m in ['12','13'] :
				try :
					date = move.date
					sunat_partner_code = move.move_id.partner_id.l10n_latam_identification_type_id.l10n_pe_vat_code or ''
					sunat_partner_vat = move.move_id.partner_id.vat or ''
					sunat_partner_name = move.move_id.partner_id.legal_name or move.move_id.partner_id.name or 'varios'
					#1-3
					m_03.extend([
						date.strftime('%Y%m%d'),
						str(move.id),
						'M' + str(move.move_id.id).rjust(9,'0'),
					])
					#4-6
					m_03.extend([
						sunat_partner_code,
						sunat_partner_vat,
						sunat_partner_name,
					])
					#7-10
					m_03.extend([
						date.strftime('%d/%m/%Y'),
						format(abs(move.balance), '.2f'),
						'1',
						'',
					])
				except Exception as e:
					_logging.info('error en lineaaaaaaaaaaaaaa 678')
					_logging.info(e)
					m_03 = []
			elif m in ['14'] :
				try :
					date = move.date
					sunat_partner_code = move.move_id.partner_id.l10n_latam_identification_type_id.l10n_pe_vat_code or ''
					sunat_partner_vat = move.move_id.partner_id.vat or ''
					sunat_partner_name = move.move_id.partner_id.legal_name or move.move_id.partner_id.name or 'varios'
					#1-3
					m_04.extend([
						date.strftime('%Y%m%d'),
						str(move.id),
						'M' + str(move.move_id.id).rjust(9,'0'),
					])
					#4-6
					m_04.extend([
						sunat_partner_code,
						sunat_partner_vat,
						sunat_partner_name,
					])
					#7-10
					m_04.extend([
						date.strftime('%d/%m/%Y'),
						format(abs(move.balance), '.2f'),
						'1',
						'',
					])
				except :
					_logging.info('error en lineaaaaaaaaaaaaaa 706')
					m_04 = []
			elif m in ['16','17'] :
				try :
					date = move.date
					sunat_partner_code = move.move_id.partner_id.l10n_latam_identification_type_id.l10n_pe_vat_code or ''
					sunat_partner_vat = move.move_id.partner_id.vat or ''
					sunat_partner_name = move.move_id.partner_id.legal_name or move.move_id.partner_id.name or 'varios'
					#1-3
					m_05.extend([
						date.strftime('%Y%m%d'),
						str(move.id),
						'M' + str(move.move_id.id).rjust(9,'0'),
					])
					#4-6
					m_05.extend([
						sunat_partner_code,
						sunat_partner_vat,
						sunat_partner_name,
					])
					#7-10
					m_05.extend([
						date.strftime('%d/%m/%Y'),
						format(abs(move.balance), '.2f'),
						'1',
						'',
					])
				except :
					_logging.info('error en lineaaaaaaaaaaaaaa 734')
					m_05 = []
			elif m in ['19'] :
				try :
					date = move.date
					sunat_partner_code = move.move_id.partner_id.l10n_latam_identification_type_id.l10n_pe_vat_code or ''
					sunat_partner_vat = move.move_id.partner_id.vat or ''
					sunat_partner_name = move.move_id.partner_id.legal_name or move.move_id.partner_id.name or 'varios'
					#1-3
					m_06.extend([
						date.strftime('%Y%m%d'),
						str(move.id),
						'M' + str(move.move_id.id).rjust(9,'0'),
					])
					#4-6
					m_06.extend([
						sunat_partner_code,
						sunat_partner_vat,
						sunat_partner_name,
					])
					#7-9
					m_06.extend([
						'00',
						'',
						'',
					])
					#10-13
					m_06.extend([
						date.strftime('%d/%m/%Y'),
						format(abs(move.balance), '.2f'),
						'1',
						'',
					])
				except :
					_logging.info('error en lineaaaaaaaaaaaaaa 768')
					m_06 = []
			elif m in ['41'] :
				try :
					date = move.date
					account_code = move.account_id.code.rstrip('0') or ''
					sunat_partner_code = move.move_id.partner_id.l10n_latam_identification_type_id.l10n_pe_vat_code or ''
					sunat_partner_vat = move.move_id.partner_id.vat or ''
					sunat_partner_name = move.move_id.partner_id.legal_name or move.move_id.partner_id.name or 'varios'
					partner_worker_code = move_move_id.partner_id.l10n_pe_worker_code or ''
					#1-3
					m_11.extend([
						date.strftime('%Y%m%d'),
						str(move.id),
						'M' + str(move.move_id.id).rjust(9,'0'),
					])
					#4-8
					m_11.extend([
						account_code,
						sunat_partner_code,
						sunat_partner_vat,
						partner_worker_code,
						sunat_partner_name,
					])
					#9-11
					m_11.extend([
						#date.strftime('%d/%m/%Y'),
						format(abs(move.balance), '.2f'),
						'1',
						'',
					])
				except :
					_logging.info('error en lineaaaaaaaaaaaaaa 800')
					m_11 = []
			elif m in ['42','43'] :
				try :
					date = move.date
					sunat_partner_code = move.move_id.partner_id.l10n_latam_identification_type_id.l10n_pe_vat_code or ''
					sunat_partner_vat = move.move_id.partner_id.vat or ''
					sunat_partner_name = move.move_id.partner_id.legal_name or move.move_id.partner_id.name or 'varios'
					#1-3
					m_12.extend([
						date.strftime('%Y%m%d'),
						str(move.id),
						'M' + str(move.move_id.id).rjust(9,'0'),
					])
					#4-6
					m_12.extend([
						sunat_partner_code,
						sunat_partner_vat,
						date.strftime('%d/%m/%Y'),
					])
					#7-10
					m_12.extend([
						sunat_partner_name,
						format(abs(move.balance), '.2f'),
						'1',
						'',
					])
				except :
					_logging.info('error en lineaaaaaaaaaaaaaa 828')
					m_12 = []
			elif m in ['46'] :
				try :
					date = move.date
					account_code = move.account_id.code.rstrip('0') or ''
					sunat_partner_code = move.move_id.partner_id.l10n_latam_identification_type_id.l10n_pe_vat_code or ''
					sunat_partner_vat = move.move_id.partner_id.vat or ''
					sunat_partner_name = move.move_id.partner_id.legal_name or move.move_id.partner_id.name or 'varios'
					#1-3
					m_13.extend([
						date.strftime('%Y%m%d'),
						str(move.id),
						'M' + str(move.move_id.id).rjust(9,'0'),
					])
					#4-6
					m_13.extend([
						sunat_partner_code,
						sunat_partner_vat,
						date.strftime('%d/%m/%Y'),
					])
					#7-11
					m_13.extend([
						sunat_partner_name,
						account_code,
						format(abs(move.balance), '.2f'),
						'1',
						'',
					])
				except :
					_logging.info('error en lineaaaaaaaaaaaaaa 858')
					m_13 = []
			elif m in ['47'] :
				try :
					date = move.date
					sunat_partner_code = move.move_id.partner_id.l10n_latam_identification_type_id.l10n_pe_vat_code or ''
					sunat_partner_vat = move.move_id.partner_id.vat or ''
					sunat_partner_name = move.move_id.partner_id.legal_name or move.move_id.partner_id.name or 'varios'
					#1-3
					m_14.extend([
						date.strftime('%Y%m%d'),
						str(move.id),
						'M' + str(move.move_id.id).rjust(9,'0'),
					])
					#4-6
					m_14.extend([
						sunat_partner_code,
						sunat_partner_vat,
						sunat_partner_name,
					])
					#7-9
					m_14.extend([
						format(abs(move.balance), '.2f'),
						'1',
						'',
					])
				except :
					_logging.info('error en lineaaaaaaaaaaaaaa 885')
					m_14 = []
			if m_02 :
				lines_to_write_02.append('|'.join(m_02))
			if m_03 :
				lines_to_write_03.append('|'.join(m_03))
			if m_04 :
				lines_to_write_04.append('|'.join(m_04))
			if m_05 :
				lines_to_write_05.append('|'.join(m_05))
			if m_06 :
				lines_to_write_06.append('|'.join(m_06))
			if m_11 :
				lines_to_write_11.append('|'.join(m_11))
			if m_12 :
				lines_to_write_12.append('|'.join(m_12))
			if m_13 :
				lines_to_write_13.append('|'.join(m_13))
			if m_14 :
				lines_to_write_14.append('|'.join(m_14))
		
		dict_to_write = dict()
		
		name_02 = self.get_default_filename(ple_id='030200', tiene_datos=bool(lines_to_write_02))
		lines_to_write_02.append('')
		txt_string_02 = '\r\n'.join(lines_to_write_02)
		if txt_string_02 :
			xlsx_file = StringIO(txt_string_02)
			df = pandas.read_csv(xlsx_file, sep='|', header=None)
			xlsx_file = BytesIO()
			df.to_excel(xlsx_file, name_02, index=False, header=False)
			xlsx_file = base64.b64encode(xlsx_file.getvalue())
			dict_to_write.update({
				'ple_txt_02': txt_string_02,
				'ple_txt_02_binary': base64.b64encode(txt_string_02.encode()),
				'ple_txt_02_filename': name_02 + '.txt',
				'ple_xls_02_binary': xlsx_file,
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
		name_03 = self.get_default_filename(ple_id='030300', tiene_datos=bool(lines_to_write_03))
		lines_to_write_03.append('')
		txt_string_03 = '\r\n'.join(lines_to_write_03)
		if txt_string_03 :
			xlsx_file = StringIO(txt_string_03)
			df = pandas.read_csv(xlsx_file, sep='|', header=None)
			xlsx_file = BytesIO()
			df.to_excel(xlsx_file, name_03, index=False, header=False)
			xlsx_file = base64.b64encode(xlsx_file.getvalue())
			dict_to_write.update({
				'ple_txt_03': txt_string_03,
				'ple_txt_03_binary': base64.b64encode(txt_string_03.encode()),
				'ple_txt_03_filename': name_03 + '.txt',
				'ple_xls_03_binary': xlsx_file,
				'ple_xls_03_filename': name_03 + '.xlsx',
			})
		else :
			dict_to_write.update({
				'ple_txt_03': False,
				'ple_txt_03_binary': False,
				'ple_txt_03_filename': False,
				'ple_xls_03_binary': False,
				'ple_xls_03_filename': False,
			})
		name_04 = self.get_default_filename(ple_id='030400', tiene_datos=bool(lines_to_write_04))
		lines_to_write_04.append('')
		txt_string_04 = '\r\n'.join(lines_to_write_04)
		if txt_string_04 :
			xlsx_file = StringIO(txt_string_04)
			df = pandas.read_csv(xlsx_file, sep='|', header=None)
			xlsx_file = BytesIO()
			df.to_excel(xlsx_file, name_04, index=False, header=False)
			xlsx_file = base64.b64encode(xlsx_file.getvalue())
			dict_to_write.update({
				'ple_txt_04': txt_string_04,
				'ple_txt_04_binary': base64.b64encode(txt_string_04.encode()),
				'ple_txt_04_filename': name_04 + '.txt',
				'ple_xls_04_binary': xlsx_file,
				'ple_xls_04_filename': name_04 + '.xlsx',
			})
		else :
			dict_to_write.update({
				'ple_txt_04': False,
				'ple_txt_04_binary': False,
				'ple_txt_04_filename': False,
				'ple_xls_04_binary': False,
				'ple_xls_04_filename': False,
			})
		name_05 = self.get_default_filename(ple_id='030500', tiene_datos=bool(lines_to_write_05))
		lines_to_write_05.append('')
		txt_string_05 = '\r\n'.join(lines_to_write_05)
		if txt_string_05 :
			xlsx_file = StringIO(txt_string_05)
			df = pandas.read_csv(xlsx_file, sep='|', header=None)
			xlsx_file = BytesIO()
			df.to_excel(xlsx_file, name_05, index=False, header=False)
			xlsx_file = base64.b64encode(xlsx_file.getvalue())
			dict_to_write.update({
				'ple_txt_05': txt_string_05,
				'ple_txt_05_binary': base64.b64encode(txt_string_05.encode()),
				'ple_txt_05_filename': name_05 + '.txt',
				'ple_xls_05_binary': xlsx_file,
				'ple_xls_05_filename': name_05 + '.xlsx',
			})
		else :
			dict_to_write.update({
				'ple_txt_05': False,
				'ple_txt_05_binary': False,
				'ple_txt_05_filename': False,
				'ple_xls_05_binary': False,
				'ple_xls_05_filename': False,
			})
		name_06 = self.get_default_filename(ple_id='030600', tiene_datos=bool(lines_to_write_06))
		lines_to_write_06.append('')
		txt_string_06 = '\r\n'.join(lines_to_write_06)
		if txt_string_06 :
			xlsx_file = StringIO(txt_string_06)
			df = pandas.read_csv(xlsx_file, sep='|', header=None)
			xlsx_file = BytesIO()
			df.to_excel(xlsx_file, name_06, index=False, header=False)
			xlsx_file = base64.b64encode(xlsx_file.getvalue())
			dict_to_write.update({
				'ple_txt_06': txt_string_06,
				'ple_txt_06_binary': base64.b64encode(txt_string_06.encode()),
				'ple_txt_06_filename': name_06 + '.txt',
				'ple_xls_06_binary': xlsx_file,
				'ple_xls_06_filename': name_06 + '.xlsx',
			})
		else :
			dict_to_write.update({
				'ple_txt_06': False,
				'ple_txt_06_binary': False,
				'ple_txt_06_filename': False,
				'ple_xls_06_binary': False,
				'ple_xls_06_filename': False,
			})
		name_11 = self.get_default_filename(ple_id='031100', tiene_datos=bool(lines_to_write_11))
		lines_to_write_11.append('')
		txt_string_11 = '\r\n'.join(lines_to_write_11)
		if txt_string_11 :
			xlsx_file = StringIO(txt_string_11)
			df = pandas.read_csv(xlsx_file, sep='|', header=None)
			xlsx_file = BytesIO()
			df.to_excel(xlsx_file, name_11, index=False, header=False)
			xlsx_file = base64.b64encode(xlsx_file.getvalue())
			dict_to_write.update({
				'ple_txt_11': txt_string_11,
				'ple_txt_11_binary': base64.b64encode(txt_string_11.encode()),
				'ple_txt_11_filename': name_11 + '.txt',
				'ple_xls_11_binary': xlsx_file,
				'ple_xls_11_filename': name_11 + '.xlsx',
			})
		else :
			dict_to_write.update({
				'ple_txt_11': False,
				'ple_txt_11_binary': False,
				'ple_txt_11_filename': False,
				'ple_xls_11_binary': False,
				'ple_xls_11_filename': False,
			})
		name_12 = self.get_default_filename(ple_id='031200', tiene_datos=bool(lines_to_write_12))
		lines_to_write_12.append('')
		txt_string_12 = '\r\n'.join(lines_to_write_12)
		if txt_string_12 :
			xlsx_file = StringIO(txt_string_12)
			df = pandas.read_csv(xlsx_file, sep='|', header=None)
			xlsx_file = BytesIO()
			df.to_excel(xlsx_file, name_12, index=False, header=False)
			xlsx_file = base64.b64encode(xlsx_file.getvalue())
			dict_to_write.update({
				'ple_txt_12': txt_string_12,
				'ple_txt_12_binary': base64.b64encode(txt_string_12.encode()),
				'ple_txt_12_filename': name_12 + '.txt',
				'ple_xls_12_binary': xlsx_file,
				'ple_xls_12_filename': name_12 + '.xlsx',
			})
		else :
			dict_to_write.update({
				'ple_txt_12': False,
				'ple_txt_12_binary': False,
				'ple_txt_12_filename': False,
				'ple_xls_12_binary': False,
				'ple_xls_12_filename': False,
			})
		name_13 = self.get_default_filename(ple_id='031300', tiene_datos=bool(lines_to_write_13))
		lines_to_write_13.append('')
		txt_string_13 = '\r\n'.join(lines_to_write_13)
		if txt_string_13 :
			xlsx_file = StringIO(txt_string_13)
			df = pandas.read_csv(xlsx_file, sep='|', header=None)
			xlsx_file = BytesIO()
			df.to_excel(xlsx_file, name_13, index=False, header=False)
			xlsx_file = base64.b64encode(xlsx_file.getvalue())
			dict_to_write.update({
				'ple_txt_13': txt_string_13,
				'ple_txt_13_binary': base64.b64encode(txt_string_13.encode()),
				'ple_txt_13_filename': name_13 + '.txt',
				'ple_xls_13_binary': xlsx_file,
				'ple_xls_13_filename': name_13 + '.xlsx',
			})
		else :
			dict_to_write.update({
				'ple_txt_13': False,
				'ple_txt_13_binary': False,
				'ple_txt_13_filename': False,
				'ple_xls_13_binary': False,
				'ple_xls_13_filename': False,
			})
		name_14 = self.get_default_filename(ple_id='031400', tiene_datos=bool(lines_to_write_14))
		lines_to_write_14.append('')
		txt_string_14 = '\r\n'.join(lines_to_write_14)
		if txt_string_14 :
			xlsx_file = StringIO(txt_string_14)
			df = pandas.read_csv(xlsx_file, sep='|', header=None)
			xlsx_file = BytesIO()
			df.to_excel(xlsx_file, name_14, index=False, header=False)
			xlsx_file = base64.b64encode(xlsx_file.getvalue())
			dict_to_write.update({
				'ple_txt_14': txt_string_14,
				'ple_txt_14_binary': base64.b64encode(txt_string_14.encode()),
				'ple_txt_14_filename': name_14 + '.txt',
				'ple_xls_14_binary': xlsx_file,
				'ple_xls_14_filename': name_14 + '.xlsx',
			})
		else :
			dict_to_write.update({
				'ple_txt_14': False,
				'ple_txt_14_binary': False,
				'ple_txt_14_filename': False,
				'ple_xls_14_binary': False,
				'ple_xls_14_filename': False,
			})
		
		dict_to_write.update({
			'date_generated': str(fields.Datetime.now()),
		})
		res = self.write(dict_to_write)
		return res
