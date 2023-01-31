# -*- coding: utf-8 -*-
{
	'name': "SOLSE CPE Guias",

	'summary': """
		Emision de guias electronicos a SUNAT - Perú""",

	'description': """
		Facturación electrónica - Perú 
		Emision de guias electronicos a SUNAT - Perú
	""",

	'author': "F & M Solutions Service S.A.C",
	'website': "http://www.solse.pe",
	'category': 'Financial',
	'version': '0.6',

	'depends': [
		'stock',
		'fleet',
		'account',
		'account_fleet',
		'product_expiry',
		'solse_pe_cpe',
	],
	'data': [
		'security/ir.model.access.csv',
		'views/pe_sunat_eguide_view.xml',
		'views/company_view.xml',
		'views/stock_view.xml',
		'views/report_invoice.xml',
		#'views/res_partner.xml',
		'data/sunat_eguide_data.xml',
		#'report/report_picking.xml',
		'report/report_guia.xml',
		
	],
	'installable': True,
	'price': 210,
	'currency': 'USD',
}