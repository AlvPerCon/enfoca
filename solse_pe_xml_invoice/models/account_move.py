# -*- coding: utf-8 -*-

from odoo import models, fields, api

class ClaseFactura(models.Model):
	_inherit = "account.move"

	xml_import_id = fields.Many2one("scpe.pe.purchase.import", "Factura importar (Compra)")
	xml_sale_import_id = fields.Many2one("scpe.pe.sale.import", "Factura importar (Venta)")
	datas_fname = fields.Char("Nombre xml")
	data_xml = fields.Binary(string="XML")
	datas_fname_pdf = fields.Char("Nombre pdf")
	data_pdf = fields.Binary(string="PDF")
