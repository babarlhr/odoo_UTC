# -*- coding: utf-8 -*-
{
    'name': "HR Timesheet ",

    'summary': """HR Timesheet""",

    'description': """
        HR Timesheet
    """,

    'author': "Tungnn",
    'website': "http://www.izisolution.vn",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/openerp/addons/base/module/module_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'hr', 'sc_hr_employee'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        # 'views/view_menu_root.xml',
        'views/hr_shift_views.xml',
        'views/hr_change_shift_view.xml',
        'views/hr_employee_going_on_business_view.xml',
        'views/hr_employee_have_child_view.xml',
        'views/hr_overtime_view.xml',
        'views/hr_employee_leave.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo.xml',
    ],

    'qweb': [
        'static/src/xml/shift_assign_details.xml',
    ],
}
