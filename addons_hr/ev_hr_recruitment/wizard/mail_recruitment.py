# -*- coding: utf-8 -*-
from odoo import fields, models, api, osv
from odoo.tools.translate import _
from datetime import datetime, timedelta


class mail_recruitment(models.TransientModel):
    _name = 'mail.recruitment'
    _inherit = ['mail.thread', 'mail.mail']
    email_to = fields.Char(string='Email to')
    email_cc = fields.Char(string='Email cc')
    subject = fields.Char(string='Subject')
    interview_id = fields.Integer(string='Interview')
    applicant_id = fields.Integer(string="Applicant")
    list_id = fields.Integer(string='List')


    def def_send_mail_working(self, applicant_id, interview_id, list_id):
        applicant_list = self.env['list.send.mail.applicant.interview'].search([('id', '=', list_id)])
        interview_line = self.env['hr.interview.line'].search([('applicant_id', '=', applicant_id), ('interview_id', '=', interview_id)])
        date_work = datetime.strptime(applicant_list.date_work, '%Y-%m-%d')
        date_expired = datetime.strptime('2018-01-01', '%Y-%m-%d')
        if applicant_list.date_expired:
            date_expired = datetime.strptime(applicant_list.date_expired, '%Y-%m-%d')
        interview_name = interview_line.interview_id.name
        arr_applicant_name = interview_line.applicant_id.partner_name.strip().split()
        applicant_name = _(arr_applicant_name[(len(arr_applicant_name) - 1)])
        gender = interview_line.applicant_id.gender == 'NU' and "Ms" or "Mr"

        day = date_work.strftime("%A")
        print('interview_line.time_interview' + str(interview_line.time_interview))
        print('self._context' + str(self._context))
        if day == 'Monday':
            day = _('thứ 2')
        elif day == 'Tuesday':
            day = _('thứ 3')
        elif day == 'Wednesday':
            day = _('thứ 4')
        elif day == 'Thursday':
            day = _('thứ 5')
        elif day == 'Friday':
            day = _('thứ 6')
        elif day == 'Saturday':
            day = _('thứ 7')
        elif day == 'Sunday':
            day = _('chủ nhật')
        date = date_work.strftime("%d/%m/%Y")
        date_exp = date_expired.strftime("%d/%m/%Y")
        job_name = _(interview_line.applicant_id.job_id.name)

        def_send_mail_working = {
            "applicant_name": applicant_name,
            "interview_name": interview_name,
            "gender": gender,
            "day": day,
            "date": date,
            "date_exp": date_exp,
            "job_name": job_name,
        }
        return def_send_mail_working



    def obj_mail_invite_to_interview(self, applicant_id, interview_id):
        # print 'interview_id' + str(interview_id)
        interview_line = self.env['hr.interview.line'].search([('applicant_id', '=', applicant_id), ('interview_id', '=', interview_id)])
        time_interview = datetime.strptime(interview_line.time_interview, '%Y-%m-%d %H:%M:%S') + timedelta(hours=7)
        print('interview_line.applicant_id: ' + str(interview_line))
        interview_name = interview_line.interview_id.name
        arr_applicant_name = interview_line.applicant_id.partner_name.strip().split()
        applicant_name = _(arr_applicant_name[(len(arr_applicant_name) - 1)])
        gender = interview_line.applicant_id.gender == 'NU' and "Ms" or "Mr"
        time = time_interview.strftime("%H:%M")

        day = time_interview.strftime("%A")
        print('interview_line.time_interview' + str(interview_line.time_interview))
        print('self._context' + str(self._context))
        if day == 'Monday':
            day = _('thứ 2')
        elif day == 'Tuesday':
            day = _('thứ 3')
        elif day == 'Wednesday':
            day = _('thứ 4')
        elif day == 'Thursday':
            day = _('thứ 5')
        elif day == 'Friday':
            day = _('thứ 6')
        elif day == 'Saturday':
            day = _('thứ 7')
        elif day == 'Sunday':
            day = _('chủ nhật')
        date = time_interview.strftime("%d/%m/%Y")
        job_name = _(interview_line.applicant_id.job_id.name)

        obj_mail_invite_to_interview = {
            "applicant_name": applicant_name,
            "interview_name": interview_name,
            "gender": gender,
            "time": time,
            "day": day,
            "date": date,
            "job_name": job_name,
        }
        # self._cr.execute(""" UPDATE hr_interview_line
        #                     SET is_sent_mail_invite_work = True
        #                     WHERE applicant_id = %s and interview_id = %s """, (applicant_id, interview_id,))
        return obj_mail_invite_to_interview

    def obj_mail_invite_to_work(self, applicant_id):
        interview_line = self.env['hr.interview.line'].search([('applicant_id', '=', applicant_id)])

    # --------------------#
    #   action button    #
    # --------------------#

    @api.multi
    def action_send_mail(self):
        applicant = self.env['hr.applicant'].search([('id', '=', self.applicant_id)])
        interview = self.env['hr.interview'].search([('id', '=', self.interview_id)])
        template = self.env['ir.model.data'].sudo().get_object('ev_hr_recruitment',
                                                               'template_hr_recruitment_send_mail_invite_work_form_1')
        mail_obj = self.env['mail.recruitment']
        mail = mail_obj.create({
            'email_to': applicant.applicant_email,
            'subject': _('VMT GROUP - THƯ MỜI NHẬN VIỆC'),
            'applicant_id': applicant.id,
        })

        for attachment_id in self.attachment_ids:
            query = """ INSERT INTO email_template_attachment_rel (email_template_id, attachment_id)  VALUES (%s,%s)"""
            self._cr.execute(query, (template.id, attachment_id.id))

        a = self.pool('email.template').send_mail(self._cr, 1, template.id, mail.id,
                                                  force_send=True)  # , force_send=True
        if a:
            self._cr.execute(""" UPDATE hr_interview_line
                                SET is_sent_mail_invite_work = True
                                WHERE applicant_id = %s  and interview_id = %s """, (applicant.id,interview.id))





# class mail_compose_message(osv.Model):
#     _inherit = 'mail.compose.message'
#
#     def send_mail(self, cr, uid, ids, context=None):
#         context = context or {}
#         if context.get('default_model') == 'hr.applicant':
#             context = dict(context, mail_post_autofollow=True)
#             # self.pool.get('hr.applicant').signal_workflow(cr, uid, [context['default_res_id']], 'send_rfq')
#         return super(mail_compose_message, self).send_mail(cr, uid, ids, context=context)