{
    'name': """
        Consulta Tipo de Cambio USD con Integración a Migo Perú
    """,

    'summary': """
        Permite obtener el tipo de cambio Compra y Venta USD mediante una integración con Migo.
    """,

    'description': """
       
    """,

    'author': 'Develogers',
    'website': 'https://develogers.com',
    'support': 'especialistas@develogers.com',
    'live_test_url': 'https://demoperu.develogers.com',
    'license': 'LGPL-3',

    'category': 'Accounting',
    'version': '14.0',

    'price': 49.99,
    'currency': 'EUR',
    
    'depends': [
        'base',
        'dv_l10n_latam_currency_multirate'
    ],

    'data': [
        'views/res_company_views.xml',
        'views/res_currency_views.xml',
        'data/autoupdate.xml',
    ],

    'images': ['static/description/banner.gif'],

    'application': True,
    'installable': True,
    'auto_install': False,
}
