# -*- coding: utf-8 -*-

{
	'name': 'Campo calculado inserta ruc en facturación',
	'version': '14.0.1.0.0',
	'category': 'Extra Tools',
	'summary': 'Muestra el ruc en el formulario de facturación',
	'author': 'Alvpercon',
	'website': 'https://www.alvpercon.com',
	'depends': ['account'],
	'data': [
		
		'views/account_move_view.xml',
	],
	'installable': True,
	'sequence': 1,
}