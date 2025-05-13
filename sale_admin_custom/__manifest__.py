{
    'name': 'Sale Admin Custom',
    'version': '1.0',
    'depends': ['account','base','sale'],
    'category': 'Sales',
    'summary': 'Custom Sale Admin features and automation',
    'data': [
        'security/sale_admin_groups.xml',
        'security/ir.model.access.csv',
        'views/sale_order_views.xml',
        'views/res_config_settings_views.xml',
    ],
    'installable': True,
    'application': False,
}
