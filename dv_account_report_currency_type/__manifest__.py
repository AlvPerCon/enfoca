{
    'name': """
        Custom Account Multicurrency Revaluation Report |
        Reporte Personalizado de Revaluación de Moneda
    """,

    'summary': """
        Adds currency rate type filter on multicurrency revaluation report. |
        Agrega filtro de tipo de tasa de cambio en el reporte de revaluación de moneda.
    """,

    'description': """
        
    """,

    'author': 'Develogers ',
    'website': 'https://develogers.com',
    'support': 'especialistas@develogers.com',
    'live_test_url': 'https://demo.develogers.com',
    'license': 'LGPL-3',

    'category': 'Invoice',
    'version': '14.0',
    
    'price': 99.99,
    'currency': 'EUR',
    
    'depends': [
        'account_reports',
        'dv_l10n_latam_currency_multirate',
    ],

    'data': [
        'views/assets.xml',
        'views/account_report_templates.xml',
        'views/search_template_view.xml',
    ],
    
    'images': ['static/description/banner.gif'],
    
    'application': True,
    'installable': True,
    'auto_install': False,
}