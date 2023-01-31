{
    'name': """
        Purchase and sale Currency Rate |
        Tipo de cambio Compra y Venta para Monedas
    """,

    'summary':"""
        Allows to create currencies with different exchange rates for sale and buy. |
        Permite crear monedads con diferente tipo de cambio para venta y compra.
    """,

    'description': """
        Agrega la campos en las moenedas para crear múltiples tipos de camio para seleccionar el tipo de cambio para venta y compra.
        Adds the fields in the currencies to create multiple exchange rates for sale and buy.
    """,

    'author': 'Develogers',
    'website': 'https://develogers.com',
    'support': 'especialistas@develogers.com',
    'live_test_url': 'https://demoperu.develogers.com',
    'license': 'LGPL-3',

    'price': 39.99,
    'currency': 'EUR',

    'category': 'Account',
    'version': '14.0',

    'depends': [
        'base',
        'account',
    ],

    'data': [
        'views/account_move_views.xml',
        'views/res_currency_views.xml',
    ],
    
    'images': ['static/description/banner.gif'],
    
    'application': True,
    'installable': True,
    'auto_install': False,
}
