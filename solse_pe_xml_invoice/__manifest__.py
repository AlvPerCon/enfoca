# -*- coding: utf-8 -*-
{
	'name': "Importar Facturas desde XML",

	'summary': """
		Permite registrar facturas de forma masiva desde los xml""",

	'description': """
		Facturación electrónica - Perú 
		Permite registrar facturas de forma masiva desde los xml
	""",

	'author': "F & M Solutions Service S.A.C",
	'website': "https://www.solse.pe",
	'category': 'Financial',
	'version': '1.1',

	'depends': [
		'account',
		'solse_pe_cpe_report',
	],
	'data': [
		'security/ir.model.access.csv',
		'views/scpe_pe_purchase_view.xml',
		'views/scpe_pe_invoice_sale_view.xml',
		'views/account_move_view.xml',
		'views/menu_view.xml',
	],
	'installable': True,
	'price': 60,
	'currency': 'USD',
}