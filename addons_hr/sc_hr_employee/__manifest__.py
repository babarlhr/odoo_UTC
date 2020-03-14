# -*- coding: utf-8 -*-
{
    'name': "sc_hr_employee",

    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",

    'description': """
        Long description of module's purpose
    """,

    'author': "Tungnn",
    'website': "http://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/openerp/addons/base/module/module_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'hr', 'hr_recruitment', 'hr_attendance'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'sequence.xml',
        'views/hr_emp_view.xml',
        'views/import_template.xml',
        # 'views/hr_job_view.xml',
    ],

    # only loaded in demonstration mode
    'qweb': [
        'static/src/xml/employee_revenue_history.xml',
    ],
    'demo': [
        'demo.xml',
    ],
}