{
    'name': "Đào Tạo",

    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",

    'description': """
        Long description of module's purpose
    """,

    'author': "Tungnn",
    'website': "http://www.izisolution.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/openerp/addons/base/module/module_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'hr', 'sc_hr_employee'],

    # always loaded
    'data': [
        # 'templates.xml',
        'security/security_training.xml',
        'security/ir.model.access.csv',
        'view/birt_report_contest_session.xml',
        'view/birt_report_conment_student.xml',
        'view/birt_report_scores_consultants.xml',
        'view/birt_report_scores_expert_skincare.xml',
        'view/birt_report_skill_consultants.xml',
        'view/birt_report_skill_expert_skincare.xml',
        'view/training_course.xml',
        'view/training_session.xml',
        'view/training_session_timetable.xml',
        'view/training_contest.xml',
        'view/training_major.xml',
        'view/training_teacher.xml',
        'view/training_rating.xml',
        'view/report_contest.xml',
        'view/report_timetable.xml',
        'view/report_session.xml',
        # 'view/training_session_employee.xml',
        'view/training_session_timetable_attendance_view.xml',
        'model/training_session_timetable_attendance.xml',
        'view/level_employee_config.xml',
        'view/import_session.xml',
        'view/menuitem.xml',
        'view/template.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo.xml',
    ],
}
# -*- coding: utf-8 -*-
