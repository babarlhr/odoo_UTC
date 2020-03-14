# -*- coding: utf-8 -*-
import datetime
from odoo import fields, api, models, _
from odoo.exceptions import except_orm

STATUS_APPLICANT_SELECTION = {
    ('waiting', 'Waiting interview'),
    ('not_coming', 'Not coming interview'),
    ('pass', 'Pass'),
    ('not_pass', 'Not pass')
}

STATUS_APPLICANT_SELECTIONS = [
    ('not_employee', 'Not employee'),
    ('is_employee', 'Is employee'),
]


class interview_line(models.Model):
    _name = 'hr.interview.line'

    time_interview = fields.Datetime(string="Interview time", required=True)
    # purpose = fields.Text(string="The purpose of the interview", required=True)

    status_applicant = fields.Selection(STATUS_APPLICANT_SELECTION, default='waiting', string="Status applicant")
    note = fields.Text(string="Note")
    file_interview = fields.Binary('File Interview')
    file_interview_name = fields.Char('File Interview Name')

    interview_id = fields.Many2one('hr.interview', string="Interview", ondelete='cascade')
    applicant_id = fields.Many2one('hr.applicant', string="Applicant", required=True)

    is_sent_mail_invite_interview = fields.Boolean(string="Is sent mail invite interview", default=False)
    is_sent_mail_invite_work = fields.Boolean(string="Is sent mail invite work", default=False)
    is_sent_mail_thank = fields.Boolean(string="Is sent mail thank", default=False)
    status_employee = fields.Selection(related='applicant_id.status_applicant', readonly=True)
    work_place = fields.Many2one('res.country.state', string='Work place',related='applicant_id.work_place')
    job_id = fields.Many2one('hr.job', string='Job', related='applicant_id.job_id')
    # send = fields.Boolean(string='Send', default=False)

    _sql_constraints = [
        ('applicant_id_interview_id_uniq', 'unique(applicant_id,interview_id)', 'Không được chọn trùng ứng viên'),
    ]

    @api.multi
    def action_open_form_update_applicant(self):
        if self.is_sent_mail_invite_interview is not True:
            raise except_orm(_('Thông báo'), _('Chỉ cập nhật sau khi đã mời ứng viên phỏng vấn, ấn nút mời ứng viên phỏng vấn!'))
            return
        is_interviewer = False
        interview = self.env['hr.interview'].search([('id', '=', self.interview_id.id)])
        cr = self._cr
        employee_ids = ''
        for employee_id in interview.interviewer_ids:
            employee_ids += str(employee_id.id) + ','
        employee_ids += '0'
        query = """ SELECT RR.user_id FROM resource_resource RR
                    INNER JOIN hr_employee HE ON RR.id = HE.resource_id WHERE HE.id = ANY( string_to_array(%s, ',')::integer[])  """
        param = (str(employee_ids),)
        cr.execute(query, param)
        res = cr.dictfetchall()
        for user_id in res:
            if self._uid == user_id['user_id']:
                is_interviewer = True
                break

        if is_interviewer:
            return {
                'name': ('Update applicant'),
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'hr.interview.line',
                'view_id': False,
                'res_id': self.id,
                'type': 'ir.actions.act_window',
                'target': 'new'
            }
        else:
            raise except_orm(_('Thông báo'),
                             _('Bạn không phải là người phỏng vấn nên không thể cập nhật kết quả cho ứng viên.'))

    @api.multi
    def action_open_form_create_employee(self):
        gender = ''
        if self.applicant_id.gender == 'NU':
            gender = 'female'
        elif self.applicant_id.gender == 'NA':
            gender = 'male'
        else:
            gender = 'other'
        view = self.env.ref('ev_hr_recruitment.interview_hr_employee_inherit_view')
        return {
            'name': _('hr employee'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'hr.employee',
            'views': [(view.id, 'form')],
            'view_id': view.id,
            'target': 'new',
            'context': {'default_name': self.applicant_id.partner_name,
                        'default_work_email': self.applicant_id.applicant_email,
                        'default_work_phone': self.applicant_id.applicant_phone,
                        'default_gender': gender,
                        'default_birthday': self.applicant_id.date_of_birth,
                        'default_job_id': self.applicant_id.job_id.id,
                        'default_department_id': self.applicant_id.department_id.id,
                        'applicant_id': self.applicant_id.id,
                        }
        }

    @api.multi
    def action_update_applicant(self):
        # hr_applicant = self.env['hr.applicant'].search([('id','=', self.applicant_id.id)])
        # if hr_applicant:
        #     hr_applicant.write({'status_recruitment': str(self.status_applicant)})
        return True


    @api.multi
    def action_send_mail_invite_work(self):
        view_id = self.env.ref('ev_hr_recruitment.list_send_mail_applicant_interview_form_3', False)
        template = self.env['ir.model.data'].sudo().get_object('ev_hr_recruitment',
                                                               'template_hr_recruitment_send_mail_invite_work_form_1')

        applicant = []
        if self.applicant_id:
            applicant.append(self.applicant_id.id)
        context = {'default_applicant_ids': applicant,
                   'default_subject': 'Giấy báo trúng tuyển',
                   'default_template_id': template.id,
                   'default_interview_id': self.interview_id.id,
                   'default_body_html': template.body_html
                   }

        return {
            'name': _('Send Mail Invite'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'list.send.mail.applicant.interview',
            'views': [(view_id.id, 'form')],
            'view_id': view_id.id,
            'target': 'new',
            'context': context,
        }


    @api.multi
    def action_send_mail_thank(self):
        view_id = self.env.ref('ev_hr_recruitment.list_send_mail_applicant_interview_form_4', False)
        template = self.env['ir.model.data'].sudo().get_object('ev_hr_recruitment',
                                                               'template_hr_recruitment_send_mail_thank_1')

        applicant = []
        if self.applicant_id:
            applicant.append(self.applicant_id.id)
        context = {'default_applicant_ids': applicant,
                   'default_subject': 'THƯ CẢM ƠN',
                   'default_template_id': template.id,
                   'default_interview_id': self.interview_id.id,
                   'default_body_html': template.body_html
                   }

        return {
            'name': _('Send Mail Thank'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'list.send.mail.applicant.interview',
            'views': [(view_id.id, 'form')],
            'view_id': view_id.id,
            'target': 'new',
            'context': context,
        }
        #
        #
        # a = self.pool('email.template').send_mail(self._cr, 1, template.id, mail.id,
        #                                           force_send=True)  # , force_send=True
        #
        # if a:
        #     self._cr.execute(""" UPDATE hr_interview_line
        #                         SET is_sent_mail_thank = True
        #                         WHERE applicant_id = %s """, (self.applicant_id.id,))

    @api.onchange('time_interview')
    def onchange_time_interview(self):
        from_date_interview = self.interview_id.from_date_interview
        to_date_interview = self.interview_id.to_date_interview
        if self.time_interview and from_date_interview and to_date_interview:
            time_interview = datetime.datetime.strptime(self.time_interview, '%Y-%m-%d %H:%M:%S')
            if not from_date_interview <= str(time_interview.date()) <= to_date_interview:
                self.time_interview = False
                return {'warning': {
                            'title': _('Warning'),
                            'message': _('Thời gian phỏng vấn ứng viên phải nằm trong khoảng thời gian diễn ra đợt phỏng vấn!')
                            }
                        }

    @api.onchange('applicant_id')
    def onchange_applicant_id(self):
        if self.applicant_id:
            query = """select status_applicant from hr_applicant where id = %s"""
            self._cr.execute(query, (self.applicant_id.id,))
            res_query = self._cr.dictfetchone()
            print("nguyen vân nh " + str(res_query))
            if res_query:
                if res_query['status_applicant'] == 'is_employee':
                    raise except_orm(_('Thông báo'), _('Ứng viên này đã là nhân viên!'))
                    return

    @api.constrains('time_interview')
    def _check_time_interview(self):
        from_date_interview = self.interview_id.from_date_interview
        to_date_interview = self.interview_id.to_date_interview
        if self.time_interview and from_date_interview and to_date_interview:
            time_interview = datetime.datetime.strptime(self.time_interview, '%Y-%m-%d %H:%M:%S')
            if not from_date_interview <= str(time_interview.date()) <= to_date_interview:
                raise except_orm(_('Thông báo'), _(
                    'Thời gian phỏng vấn ứng viên phải nằm trong khoảng thời gian diễn ra đợt phỏng vấn!.' + str(
                        self.time_interview)))

    @api.model
    def default_get(self, fields):
        print("interview_line.py self._context: " + str(self._context))
        res = super(interview_line, self).default_get(fields)

        return res


        # class create_employee_from_interview(models.TransientModel):
        #     _name = 'employee.from.interview'
        #
        #     name = fields.Char(string="Name")
        #     x_join_date = fields.Date(string=_("Join Date"))
        #     status = fields.Char(string="Status")
        #     note = fields.Text(string="Note")
        #
        #     @api.multi
        #     def action_confirm_interview(self):
        #         print 'nguyen van anh'




class list_send_mail_applicant_interview(models.Model):
    _name = 'list.send.mail.applicant.interview'

    hr_recruitment_session_id = fields.Many2one('hr.recruitment.session', string='Recruiment session')
    interview_id = fields.Many2one('hr.interview', string='Interview')
    applicant_ids = fields.Many2many('hr.applicant', string="Applicant", required=True)
    body_html = fields.Html(string='Body')
    type = fields.Selection(
        selection=[('form_1', 'Form 1'), ('form_2', 'Form 2'), ('form_3', 'Form 3')], default='form_1')
    date_work = fields.Date(string='Date work')
    date_expired = fields.Date(string='Date expired')


    @api.onchange('type')
    def onchange_type(self):
        if self.type == 'form_1':
            template = self.env['ir.model.data'].sudo().get_object('ev_hr_recruitment',
                                                                   'template_hr_recruitment_send_mail_invite_work_form_1')
        elif self.type == 'form_2':
            template = self.env['ir.model.data'].sudo().get_object('ev_hr_recruitment',
                                                                   'template_hr_recruitment_send_mail_invite_work_form_2')
        elif self.type == 'form_3':
            template = self.env['ir.model.data'].sudo().get_object('ev_hr_recruitment',
                                                                   'template_hr_recruitment_send_mail_invite_work_form_3')
        self.body_html = template.body_html
        # self.template_id = template.id



    @api.multi
    def action_add_applicant(self):
        for applicant in self.applicant_ids:
            self._cr.execute('''insert into hr_applicant_hr_recruitment_session_rel (hr_recruitment_session_id,hr_applicant_id) VALUES (%s, %s)''', (self.hr_recruitment_session_id.id, applicant.id,))
    @api.multi
    def action_send(self):
        for applicant in self.applicant_ids:
            print(applicant.id)
            template = self.env['ir.model.data'].sudo().get_object('ev_hr_recruitment',
                                                                   'template_hr_recruitment_send_mail_invite_interview_7')
            mail_obj = self.env['mail.recruitment']
            mail = mail_obj.create({
                'email_to': applicant.applicant_email,
                'email_cc': 'odoo.izisolution@gmail.com',
                'subject': _('VMT GROUP_THƯ MỜI PHỎNG VẤN'),
                'applicant_id': applicant.id,
                'interview_id': self.interview_id.id,
            })
            a = self.pool('email.template').send_mail(self._cr, 1, template.id, mail.id,
                                                      force_send=True)
            if a:
                self._cr.execute(""" UPDATE hr_interview_line
                                    SET is_sent_mail_invite_interview = True
                                    WHERE applicant_id = %s and interview_id = %s """, (applicant.id,self.interview_id.id))
        if len(self.applicant_ids) == 0:
            raise except_orm(_('Thông báo'), _('Không thể mời khi chưa có ứng viên, mời thêm ứng viên!'))
    @api.multi
    def action_send_work(self):
        for applicant in self.applicant_ids:
            template = False
            if self.type == 'form_1':
                template = self.env['ir.model.data'].sudo().get_object('ev_hr_recruitment',
                                                                       'template_hr_recruitment_send_mail_invite_work_form_send_1')
            elif self.type == 'form_2':
                template = self.env['ir.model.data'].sudo().get_object('ev_hr_recruitment',
                                                                       'template_hr_recruitment_send_mail_invite_work_form_send_2')
            elif self.type == 'form_3':
                template = self.env['ir.model.data'].sudo().get_object('ev_hr_recruitment',
                                                                       'template_hr_recruitment_send_mail_invite_work_form_send_3')


            mail_obj = self.env['mail.recruitment']
            mail = mail_obj.create({
                'email_to': applicant.applicant_email,
                'email_cc': 'odoo.izisolution@gmail.com',
                'subject': _('VMT GROUP - THƯ MỜI NHẬN VIỆC'),
                'applicant_id': applicant.id,
                'interview_id': self.interview_id.id,
                'list_id': self.id,
            })
            a = self.pool('email.template').send_mail(self._cr, 1, template.id, mail.id,
                                                      force_send=True)


            if a:
                self._cr.execute(""" UPDATE hr_interview_line
                                    SET is_sent_mail_invite_work = True
                                    WHERE applicant_id = %s  and interview_id = %s """, (applicant.id, self.interview_id.id))
        if len(self.applicant_ids) == 0:
            raise except_orm(_('Thông báo'), _('Không thể gửi mail khi chưa chọn ứng viên!'))
    @api.multi
    def action_send_thank(self):
        for applicant in self.applicant_ids:
            template = self.env['ir.model.data'].sudo().get_object('ev_hr_recruitment',
                                                                   'template_hr_recruitment_send_mail_thank_1')

            mail_obj = self.env['mail.recruitment']
            mail = mail_obj.create({
                'email_to': applicant.applicant_email,
                'email_cc': 'odoo.izisolution@gmail.com',
                'subject': _('VMT GROUP - THƯ CẢM ƠN '),
                'applicant_id': applicant.id,
                'interview_id': self.interview_id.id,
                'list_id': self.id,
            })
            a = self.pool('email.template').send_mail(self._cr, 1, template.id, mail.id,
                                                      force_send=True)


            if a:
                self._cr.execute(""" UPDATE hr_interview_line
                                    SET is_sent_mail_thank = True
                                    WHERE applicant_id = %s  and interview_id = %s """, (applicant.id, self.interview_id.id))
        if len(self.applicant_ids) == 0:
            raise except_orm(_('Thông báo'), _('Không thể gửi mail khi chưa chọn ứng viên!'))
