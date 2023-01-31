# -*- coding: utf-8 -*-

{
	'name': 'Tipo de cambio del BCR en detalles de facturas',
	'version': '14.0.1.0.0',
	'category': 'Extra Tools',
	'summary': 'Automatización de tipo de cambio del BCR en lineas contables de facturas compras y ventas tomando como referencia fecha de factura Ver 1.4 04-07-2022 23:23 se agrega condicion en tipo de cambio = 0 para diario diferencia de cambio ',
	'author': 'Alvpercon',
	'website': 'https://www.alvpercon.com',
	'depends': [
		'base',
		'l10n_pe_currency',
		'account',
		'solse_pe_accountant',
	],
	'data': [
		'data/ir_cron_data.xml',
		'views/account_move_view.xml',
	],
	'installable': True,
	'sequence': 1,
}
