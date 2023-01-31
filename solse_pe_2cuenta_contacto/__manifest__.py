# -*- coding: utf-8 -*-
{
	'name': "Perú - 2Cuenta Contacto",

	'summary': """
		2Cuenta Contacto""",

	'description': """
		Agrega un nuevo campo en el cliente para los movimientos en moneda extranjera en una cuenta contable diferente a la cuenta por defecto.
	""",

	'author': "F & M Solutions Service S.A.C",
	'website': "https://www.solse.pe",
	'category': 'Financial',
	'version': '0.1.0',

	'depends': [
		'account',
		'solse_pe_edi',
	],
	'data': [
		'views/res_partner_view.xml',
	],
	'installable': True,
	'price': 30,
	'currency': 'USD',
}