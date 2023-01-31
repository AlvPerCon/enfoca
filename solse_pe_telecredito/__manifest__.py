# -*- coding: utf-8 -*-

{
	'name': 'Perú - Telecrédito',
	'version': '14.0.1.0.0',
	'category': 'Financial',
	'summary': 'Perú - Telecrédito',
	'depends': [
		'solse_pe_edi',
		'solse_pe_cpe',
	],
	'data': [
		'security/ir.model.access.csv',
		'views/telecredito_view.xml',
		'views/res_partner_view.xml',
		'wizard/pago_telecredito_view.xml',
	],
	'external_dependencies': {
		'python': [
			'pandas',
			'xlsxwriter',
		],
	},
	'auto_install': False,
	'installable': True,
	'application': True,
	'sequence': 1,
}
