# -*- coding: utf-8 -*-
{
	'name': "Perú - Contabilidad",

	'summary': """
		Contabilidad básica para Perú""",

	'description': """
		Agrega datos necesarios para la contabilidad básica en Perú
	""",

	'author': "F & M Solutions Service S.A.C",
	'website': "https://www.solse.pe",
	'category': 'Financial',
	'version': '0.4.1',

	'depends': [
		'account',
		'solse_pe_edi',
	],
	'data': [
		'views/res_config_settings_view.xml',
		'views/account_move_view.xml',
		'wizard/account_payment_register_views.xml',
	],
	'installable': True,
	'price': 690,
	'currency': 'USD',
}