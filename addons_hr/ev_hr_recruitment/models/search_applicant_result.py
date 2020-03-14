# -*- coding: utf-8 -*-
from odoo import fields, models, api, _

GENDER_SELECTION = [
    ('male', 'Male'),
    ('female', 'Female'),
    ('other', 'Other'),
]
STATUS_APPLICANT_SELECTION = {
    ('waiting', 'Waiting interview'),
    ('not_coming', 'Not coming interview'),
    ('pass', 'Pass'),
    ('not_pass', 'Not pass')
}

class history_applicant_recruitment(models.TransientModel):
    _name = 'hr.history.applicant.recruitment'

    applicant_id = fields.Many2one('hr.search.applicant.result', string='Applicant ID')
    applicant_name = fields.Char(string='Applicant name', )
    applicant_email = fields.Char(string='Applicant email', )
    phone = fields.Char(string='Phone', )
    lines = fields.One2many('hr.history.applicant.recruitment.line', 'history_id', string='Lines')

class history_applicant_recruitment_line(models.TransientModel):
    _name = 'hr.history.applicant.recruitment.line'

    history_id = fields.Many2one('hr.history.applicant.recruitment', string='History')
    recruitment_session_id = fields.Many2one('hr.recruitment.session', string='Recruitment session')
    job_name = fields.Char(string="Job name", required=True)
    interview_id = fields.Many2one('hr.interview', string='Interview')
    state = fields.Selection(STATUS_APPLICANT_SELECTION, default='draft', string="State interview")

class search_applicant_result(models.TransientModel):
    _inherit = 'hr.applicant'
    _name = 'hr.search.applicant.result'
    _order = 'partner_name asc'

    name = fields.Char(string="Subject / Application Name", required=False)
    partner_name = fields.Char(string="Applicant's Name", required=False)
    place_of_birth = fields.Char(string="Place of birth", required=False)
    date_of_birth = fields.Date(string="Date of birth", required=False)
    gender = fields.Selection(GENDER_SELECTION, default='female', required=False)
    address = fields.Char(string="Address", required=False)
    current_address = fields.Char(string="Current address", required=False)
    identity_card = fields.Char(string="Identity Card", required=False)
    place_of_issue = fields.Char(string="Place of Issue", required=False)
    date_of_issue = fields.Date(string="Date of Issue", required=False)
    applicant_phone = fields.Char(string="applicant phone", required=False)
    job_id = fields.Many2one('hr.job', string="Job title", required=False)
    file_cv = fields.Binary('File CV', required=False)

    applicant_id = fields.Integer(string="Applicant")
    search_applicant_criteria_id = fields.Many2one('hr.search.applicant.criteria')

    @api.multi
    def action_view_history(self):
        model, view_id = self.env['ir.model.data'].get_object_reference('ev_hr_recruitment', 'history_applicant_recruitment_form')
        # Tạo bản ghi hr.history.applicant.recruitment
        history = {
            'applicant_id': self.id,
            'applicant_name': self.partner_name,
            'applicant_email': self.applicant_email,
            'phone': self.applicant_phone,
        }
        history_create = self.env['hr.history.applicant.recruitment']
        history_id = history_create.create(history)

        # Truy vấn lấy dữ liệu đợt tuyển dụng
        applicant_id = self.env['hr.applicant'].search([('applicant_phone', '=', self.applicant_phone), ('id', '=', self.applicant_id), ], limit=1)
        query = "SELECT hr_recruitment_session_id FROM hr_applicant_hr_recruitment_session_rel WHERE hr_applicant_id = %s"
        self._cr.execute(query, (applicant_id.id, ))
        res = self._cr.dictfetchall()

        for item in res:
            recruitment_session_obj = self.env['hr.recruitment.session'].search([('id', '=', item['hr_recruitment_session_id'])], limit=1)
            applicant_obj = self.env['hr.applicant'].search([('applicant_phone', '=', self.applicant_phone), ('id', '=', self.applicant_id)], limit=1)
            interview_line_obj = self.env['hr.interview.line'].search([('applicant_id', '=', applicant_obj.id),])

            if interview_line_obj:
                for item in interview_line_obj:
                    interview_obj = self.env['hr.interview'].search([('id', '=', item.interview_id.id),
                                                                     ('recruitment_session_id', '=',
                                                                      recruitment_session_obj.id)])
                    if interview_obj:
                        history_line = {
                            'history_id': history_id and history_id.id or False,
                            'recruitment_session_id': recruitment_session_obj and recruitment_session_obj.id or False,
                            'job_name': applicant_obj.job_id.name if applicant_obj.job_id else '',
                            'interview_id': interview_obj and interview_obj.id or False,
                            'state': item.status_applicant,
                        }
                        history_lines_create = self.env['hr.history.applicant.recruitment.line']
                        history_lines_create.create(history_line)
                    else:
                        pass
            else:
                history_line = {
                    'history_id': history_id and history_id.id or False,
                    'recruitment_session_id': recruitment_session_obj and recruitment_session_obj.id or False,
                    'job_name': applicant_obj.job_id.name if applicant_obj.job_id else '',
                    'interview_id': '',
                    'state': '',
                }
                history_lines_create = self.env['hr.history.applicant.recruitment.line']
                history_lines_create.create(history_line)

        return {
            'name': 'History',
            'type': 'ir.actions.act_window',
            'res_model': 'hr.history.applicant.recruitment',
            'view_mode': 'form',
            'view_id': view_id,
            'target': 'new',
            'res_id': history_id.id,
        }

    @api.multi
    def action_view_detail_applicant(self):
        print("search_applicant_result.py > def action_view_detail_applicant")
        # view = self.env.ref('ev_hr_recruitment.search_applicant_result_form_view')
        view = self.env.ref('ev_hr_recruitment.view_applicant_form')
        return {
            'name': ('Applicant'),
            'res_id': self.applicant_id,
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'hr.applicant',
            'view_id': view.id,
            'type': 'ir.actions.act_window',
            'target': 'new'
        }
