{
    'name': """
        Crear Factura de Proveedor desde XML
    """,

    'summary': """
        SUMMARY. |
    """,

    'description': """
        DESCRIPTION. |
    """,

    'author': 'Develogers',
    'website': 'https://develogers.com',
    'support': 'especialistas@develogers.com',
    'live_test_url': 'https://demo.develogers.com',
    'license': 'LGPL-3',

    'category': 'Invoice',
    'version': '14.0',

    'depends': [
        'base',
        'l10n_pe',
        'account',
    ],

    'data': [
        'security/ir.model.access.csv',
        'views/account_move_views.xml',
        'views/invoice_supplier_import_views.xml',
        'views/menuitem_views.xml',
    ],

    "assets": {
    },

    'images': ['static/description/banner.gif'],

    'application': True,
    'installable': True,
    'auto_install': False,
    'sequence': 1,
}
