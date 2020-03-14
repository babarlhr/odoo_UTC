# -*- coding: utf-8 -*-
from odoo import models, api, fields, _
from odoo.exceptions import ValidationError, except_orm

STATE_RECRUITMENT_SESSION_SELECTION = [

    ('draft', 'Draft'),
    # ('send_required', 'Send required'),
    # ('confirm', 'Confirm'),
    ('choose_applicant', 'Choose applicant'),
    ('interview', 'Interview'),
    ('done', 'Done'),
    ('cancel', 'Cancel'),
]


class recruitment_session(models.Model):
    _name = 'hr.recruitment.session'

    name = fields.Char(string="Name" , copy=False)
    code = fields.Char(string="Code", default="\\", copy=False)
    time_start_receive_resumes = fields.Date(string="Time start receive resumes", copy=False)
    time_end_receive_resumes = fields.Date(string="Time end receive resumes", copy=False)
    receiver_id = fields.Many2one('hr.employee', string="Receiver", required=True)
    receiver_email = fields.Char(string="Email receiver")
    receiver_phone = fields.Char(string="Phone receiver")
    location_recruitment = fields.Char(string="Location recruitment", required=True)
    note = fields.Text(string="Note", copy=False)
    recruitment_session_line_ids = fields.One2many('hr.recruitment.session.line', 'recruitment_session_id',
                                                   string="Detail", copy=True)
    recruitment_request_ids = fields.Many2many('hr.recruitment.request',
                                               'hr_recruitment_request_hr_recruitment_session_rel',
                                               'recruitment_session_id', 'recruitment_request_id',
                                               string="Recruitment request", )
    applicant_ids = fields.Many2many('hr.applicant', string="Applicants", copy=False)
    interview_ids = fields.One2many('hr.interview', 'recruitment_session_id', string="Interviews", copy=False)
    state = fields.Selection(STATE_RECRUITMENT_SESSION_SELECTION, default='draft', string="State recruitment session")
    cost = fields.Float(string='Cost' , copy=False)

    _sql_constraints = [
        ('code_uniq', 'unique(code)', 'Không được trùng Mã đợt tuyển dụng!'),
    ]




    @api.multi
    def back_to_draft(self):
        self.state = 'draft'

    @api.multi
    def action_add_applicant(self):
        view_id = self.env.ref('ev_hr_recruitment.list_send_mail_applicant_interview_form_2', False)
        return {
            'name': _('List Applicant'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'list.send.mail.applicant.interview',
            'views': [(view_id.id, 'form')],
            'view_id': view_id.id,
            'target': 'new',
            'context': {'default_hr_recruitment_session_id': self.id,}
        }
    @api.multi
    def action_add_interview(self):
        view_id = self.env.ref('ev_hr_recruitment.view_interview_form', False)
        return {
            'name': _('List Applicant'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'hr.interview',
            'views': [(view_id.id, 'form')],
            'view_id': view_id.id,
            'target': 'current',
            'context': {'default_recruitment_session_id': self.id,}
        }

    # @api.multi
    # def confirm(self):
    #     if len(self.recruitment_session_line_ids) > 0:
    #         self.state = 'confirm'
    #     else:
    #         raise except_orm(_('Thông báo'), _('Chưa thêm chi tiết tuyển dụng.'))

    @api.multi
    def start(self):
        if len(self.recruitment_session_line_ids) > 0:
            self.state = 'choose_applicant'
        else:
            raise except_orm(_('Thông báo'), _('Chưa thêm chi tiết tuyển dụng.'))

    @api.multi
    def interview(self):
        if len(self.applicant_ids) > 0:
            self.state = 'interview'
        else:
            raise except_orm(_('Thông báo'), _('Chưa chọn ứng viên.'))

    @api.multi
    def done(self):
        user_obj = self.env['res.users']
        is_hr_manager = user_obj.has_group('base.group_hr_user')

        if is_hr_manager:
            print('Done')
        else:
            if self.create_uid.id != self._uid:
                raise except_orm('Thông báo', 'Chỉ nhân sự mới có quyền hoàn thành đợt tuyển dụng!')

        if len(self.interview_ids) > 0:
            for interview in self.interview_ids:
                if interview.state == 'done':
                    self.state = 'done'
                else:
                    raise except_orm(_('Thông báo'), _('Không thể hoàn thành đợt tuyển dụng khi đợt phỏng vấn chưa hoàn thành.'))
        else:
            raise except_orm(_('Thông báo'), _('Chưa tạo đợt phỏng vấn.'))

    @api.multi
    def cancel(self):
        user_obj = self.env['res.users']
        is_hr_manager = user_obj.has_group('base.group_hr_user')

        if is_hr_manager:
            print('Done')
        else:
            if self.create_uid.id != self._uid:
                raise except_orm('Thông báo', 'Chỉ nhân sự mới có quyền hủy đợt tuyển dụng!')
        self.state = 'cancel'

    @api.multi
    def action_update_recruitment_request_line(self):
        recruitment_session_lines = []
        for recruitment_request in self.recruitment_request_ids:
            print("recruitment_request: " + str(recruitment_request))
            if recruitment_request.state != 'cancel':
                for recruitment_request_line in recruitment_request.recruitment_request_line_ids:
                    recruitment_session_lines.append({
                        'job_id': recruitment_request_line.job_id,
                        'department_id': recruitment_request.department_id,
                        'qty': recruitment_request_line.qty,
                        'number_of_years_experience': 0,
                    })
            else:
                query = '''delete from hr_recruitment_request_hr_recruitment_session_rel WHERE  recruitment_session_id = %s and recruitment_request_id =  %s'''
                self._cr.execute(query, (self.id,recruitment_request.id ))
                # leave_history_use = self._cr.dictfetchone()
        self.recruitment_session_line_ids.unlink()
        self.recruitment_session_line_ids = recruitment_session_lines

    @api.onchange('cost')
    def onchange_cost(self):
        if self.cost:
            if self.cost < 0:
                res = {'warning': {
                    'title': _('Warning'),
                    'message': _('Chi phí không thể nhỏ hơn 0, mời nhập lại!')
                }
                }
                self.cost = 0
                return res

    @api.onchange('receiver_id')
    def onchange_receiver(self):
        self.receiver_email = self.receiver_id.work_email
        self.receiver_phone = self.receiver_id.mobile_phone

    @api.onchange('time_end_receive_resumes')
    def onchange_time_end_receive_resumes(self):
        res = {}
        if self.time_start_receive_resumes and self.time_start_receive_resumes > self.time_end_receive_resumes:
            res = {'warning': {
                'title': _('Warning'),
                'message': _('Time start receive resumes \'' + str(
                    self.time_start_receive_resumes) + '\' must be less than Time end receive resumes \'' + str(
                    self.time_end_receive_resumes) + '\' .')
            }
            }
        if res:
            return res

    @api.onchange('time_start_receive_resumes')
    def onchange_time_start_receive_resumes(self):
        res = {}
        if self.time_end_receive_resumes and self.time_start_receive_resumes > self.time_end_receive_resumes:
            res = {'warning': {
                'title': _('Warning'),
                'message': _('Time start receive resumes \'' + str(
                    self.time_start_receive_resumes) + '\' must be less than Time end receive resumes \'' + str(
                    self.time_end_receive_resumes) + '\' .')
            }
            }
        if res:
            return res

    @api.constrains('time_end_receive_resumes', 'time_start_receive_resumes')
    def _check_time_get_profile(self):

        if self.time_start_receive_resumes > self.time_end_receive_resumes:
            raise ValidationError('Time start receive resumes \'' + str(
                self.time_start_receive_resumes) + '\' must be less than Time end receive resumes \'' + str(
                self.time_end_receive_resumes) + '\' .')

    @api.constrains('time_start_receive_resumes', 'recruitment_request_ids')
    def _check_time_and_request(self):
        for r in self.recruitment_request_ids:
            if self.time_start_receive_resumes < r.request_date:
                raise except_orm(_('Thông báo'), _('Đợt phỏng vấn '+ str(r.name) + ' chưa đến ngày bắt đầu!!!!!'))

    @api.model
    def create(self, vals):
        vals['code'] = self.pool.get('ir.sequence').next_by_code(self.env.cr, self.env.uid,
                                                                 'hr_recruitment_session_name_seq')
        return super(recruitment_session, self).create(vals)
