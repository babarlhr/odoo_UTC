# -*- coding: utf-8 -*-
{
    'name': "HR Holiday ",

    'summary': """HR Holiday""",

    'description': """
        HR Holiday
    """,

    'author': "Tungnn",
    'website': "http://www.izisolution.vn",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/openerp/addons/base/module/module_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'ev_hr_timesheet', 'hr_holidays'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/root_view.xml',
        'views/emloyee_holiday_view.xml',
        'views/employee_holiday_type_view.xml',
        'templates.xml',
        'demo.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo.xml',
    ],
}
