{
    'name': """
        Custom Accounting Reports Community |
    """,

    'summary': """
        
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
    
    'price': 199.99,
    'currency': 'EUR',
    
    'depends': [
        'account',
    ],

    'data': [
        'security/ir.model.access.csv',
        'views/assets.xml',
        'views/account_report_view.xml',
        'views/report_financial.xml',
        'views/search_template_view.xml',
        'views/partner_view.xml',
        'views/res_config_settings_views.xml',
        'views/account_activity.xml',
    ],
    
    'qweb': [
        'static/src/xml/account_report_template.xml',
    ],
    
    'images': ['static/description/banner.gif'],
    
    'application': True,
    'installable': True,
    'auto_install': False,
}