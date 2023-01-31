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

class PLEReport13(models.Model) :
	_name = 'ple.report.13'
	_description = 'PLE 13 - Estructura del Registro de Inventario Permanente Valorizado'
	_inherit = 'ple.report.templ'
	
	year = fields.Integer(required=True)
	month = fields.Selection(selection_add=[], required=True)
	
	line_ids = fields.Many2many(comodel_name='stock.picking', string='Entregas', readonly=True)
	
	ple_txt_01 = fields.Text(string='Contenido del TXT 13.1')
	ple_txt_01_binary = fields.Binary(string='TXT 13.1')
	ple_txt_01_filename = fields.Char(string='Nombre del TXT 13.1')
	ple_xls_01_binary = fields.Binary(string='Excel 13.1')
	ple_xls_01_filename = fields.Char(string='Nombre del Excel 13.1')
	
	def get_default_filename(self, ple_id='130100', tiene_datos=False) :
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
		current_offset = fields.Datetime.context_timestamp(self, fields.Datetime.now()).utcoffset()
		start = datetime.datetime.combine(start, datetime.time.min) - current_offset
		end = datetime.datetime.combine(end, datetime.time.min) - current_offset
		lines = self.env.ref('base.pe').id
		lines = [
			('company_id','=',self.company_id.id),
			('company_id.partner_id.country_id','=',lines),
			('picking_type_id.code','in',['incoming','outgoing']),
			('state','=','done'),
			('date_done','>=',str(start)),
			('date_done','<=',str(end)),
		]
		lines = self.env[self.line_ids._name].sudo().search(lines, order='date_done asc')
		#new_lines = self.env[self.line_ids._name] | lines
		#for line in new_lines :
		#    if 'product' not in line.move_line_ids_without_package.mapped('product_id').mapped('type') :
		#        lines -= line
		self.line_ids = lines
		return res
	
	def generate_report(self) :
		res = super().generate_report()
		lines_to_write = []
		lines = self.line_ids.sudo()
		initial_quantity = 0
		initial_cost = 0
		for move in lines :
			products = move.move_line_ids_without_package
			#products = products.filtered(lambda r: r.product_id.type == 'product')
			products = products.mapped('product_id')
			for product in products :
				product_lines = move.move_line_ids_without_package.filtered(lambda r: r.product_id == product)
				product_quantity = sum(product_lines.mapped('qty_done'))
				if (move.picking_type_id.code == 'outgoing') and (product_quantity != 0) :
					product_quantity = 0 - product_quantity
				product_cost = product.standard_price
				initial_cost = initial_cost * initial_quantity
				initial_quantity = initial_quantity + product_quantity
				initial_cost = initial_quantity and ((initial_cost + (product_quantity * product_cost)) / initial_quantity) or 0
				m_1 = []
				try :
					sunat_number = move.pe_guide_number.split('-')
					move_id = (product_lines and product_lines[0] or move).id
					move_name = product.display_name
					if move_name :
						move_name = move_name.replace('\r', ' ').replace('\n', ' ').split()
						move_name = ' '.join(move_name).strip()
					if not move_name :
						move_name = 'Producto'
					move_name = move_name[:200]
					date = move.date_done
					#1-3
					m_1.extend([
						date.strftime('%Y%m00'),
						str(move_id),
						('M'+str(move_id).rjust(9,'0')),
					])
					#4-9
					"""m_1.extend([
						'9999',
						'1',
						'01',
						'1',
						product.default_code and product.default_code[:24] or '',
						(product.l10n_pe_sunat_product_id or (product.company_id or self.company_id).l10n_pe_sunat_product_id).code or '10000000',
					])"""
					m_1.extend([
						'9999',
						'1',
						'01',
						'1',
						product.default_code and product.default_code[:24] or '',
						product.pe_code_osce or '10000000',
					])
					#10-11
					m_1.extend([
						date.strftime('%d/%m/%Y'),
						'09',
					])
					#12-13
					m_1.extend(sunat_number)
					#14-17
					m_1.extend([
						#move.handling_code.code or '01',
						move.pe_transfer_code or '01',
						move_name,
						#(product_id.uom_id.unece_code == 'C62') and 'NIU' or product_id.uom_id.unece_code or 'NIU',
						product.uom_id.sunat_code or 'NIU',
						'1',
					])
					#18-20
					if move.picking_type_id.code == 'incoming' :
						m_1.extend([
							str(product_quantity),
							str(product_cost),
							str(product_quantity * product_cost),
						])
					else :
						m_1.extend([
							'0.00',
							'0.00',
							'0.00',
						])
					#21-23
					if move.picking_type_id.code == 'outgoing' :
						m_1.extend([
							str(product_quantity),
							str(product_cost),
							str(product_quantity * product_cost),
						])
					else :
						m_1.extend([
							'0.00',
							'0.00',
							'0.00',
						])
					#24-26
					m_1.extend([
						str(initial_quantity),
						str(initial_cost),
						str(initial_quantity * initial_cost),
					])
					#27-28
					m_1.extend(['1', ''])
				except Exception as e:
					_logging.info('error en lineaaaaaaaaaaaaaa 2098')
					_logging.info(e)
					m_1 = []
				if m_1 :
					lines_to_write.append('|'.join(m_1))
		name_01 = self.get_default_filename(ple_id='130100', tiene_datos=bool(lines_to_write))
		lines_to_write.append('')
		txt_string_01 = '\r\n'.join(lines_to_write)
		dict_to_write = dict()
		if txt_string_01 :
			xlsx_file = StringIO(txt_string_01)
			df = pandas.read_csv(xlsx_file, sep='|', header=None)
			xlsx_file = BytesIO()
			df.to_excel(xlsx_file, name_01, index=False, header=False)
			xlsx_file = base64.b64encode(xlsx_file.getvalue())
			dict_to_write.update({
				'ple_txt_01': txt_string_01,
				'ple_txt_01_binary': base64.b64encode(txt_string_01.encode()),
				'ple_txt_01_filename': name_01 + '.txt',
				'ple_xls_01_binary': xlsx_file,
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
		dict_to_write.update({
			'date_generated': str(fields.Datetime.now()),
		})
		res = self.write(dict_to_write)
		return res
