# -*- coding: utf-8 -*-
{
    'name': "ev_hr_recruitment",

    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",

    'description': """
        Long description of module's purpose
    """,

    'author': "Tungnn (IziSolution)",
    'website': "http://www.izisolution.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/openerp/addons/base/module/module_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'hr_recruitment'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'templates.xml',
        # 'views/root_view.xml',
        'views/history_applicant_recruiment.xml',
        # 'views/job_position_view.xml',
        # 'views/job_view.xml',
        'views/recruitment_request_view.xml',
        # 'views/interview_questions.xml',
        # 'views/recruitment_request_line_view.xml',
        'views/recruitment_session_view.xml',
        # 'views/major_view.xml',
        'views/interview_view.xml',
        # 'views/interview_line_view.xml',
        'views/search_applicant_view.xml',
        # 'views/source_view.xml',
        # 'views/hr_employee_inherit.xml',
        # # templates
        # 'templates/mail.xml',
        'views/import_applicant.xml',
        # 'views/inherit_mail_compose_message.xml',
        # 'views/list_send_mail_applicant_interview.xml',
        # 'views/applicant.question.xml',
        #
        # #wizard
        # 'wizard/mail_recruitment_view.xml',
        'views/applicant_view.xml',
        'views/inherit_hr_job.xml',
        'security/security_recruitment.xml',

    ],
    # only loaded in demonstration mode
    'demo': [
        'demo.xml',
    ],
}