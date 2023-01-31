# -*- coding: utf-8 -*-

{
	'name': 'Campo Glosa en Factura',
	'version': '14.0.1.0.0',
	'category': 'Extra Tools',
	'summary': 'Inserta campo glosa en encabezado de Factura y en detalles de la factura ',
	'author': 'Alvpercon',
	'website': 'https://www.alvpercon.com',
	'depends': [
		'base',
		'l10n_pe_currency',
		'account',
	],
	'data': [
		
		'views/account_move_view.xml',
	],
	'installable': True,
	'sequence': 1,
}
