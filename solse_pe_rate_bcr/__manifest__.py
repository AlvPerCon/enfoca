# -*- coding: utf-8 -*-

{
	'name': 'Tipo de cambio del BCR',
	'version': '14.0.1.0.0',
	'category': 'Extra Tools',
	'summary': 'Automatización de tipo de cambio del BCR',
	'author': 'MSTECH',
	'website': 'https://www.mstech.pe',
	'depends': [
		'base',
		'l10n_pe_currency',
	],
	'data': [
		'data/ir_cron_data.xml',
		'views/account_move_view.xml',
	],
	'installable': True,
	'sequence': 1,
}
