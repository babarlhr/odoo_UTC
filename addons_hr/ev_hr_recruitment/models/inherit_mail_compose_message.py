# -*- coding: utf-8 -*-

from odoo import api, fields, models, _, osv
from odoo.exceptions import except_orm, Warning, RedirectWarning, ValidationError
import logging
_logger = logging.getLogger(__name__)

class inherit_mail_compose_message(models.TransientModel):
    _inherit = 'mail.compose.message'

    interview_id = fields.Many2one('hr.interview', string='Interview')
    applicant_ids = fields.Many2many('hr.applicant','mail_compose_message_hr_applicant_rel', 'message_id','hr_applicant_id', string='Applicants')


    # @api.onchange('type_mail')
    # def onchange_type(self):
    #     template_id = False
    #     if self.type_mail == 'form_1':
    #         template_id = self.env.ref('ev_hr_recruitment.template_hr_recruitment_send_mail_invite_work_form_1', False)
    #     elif self.type_mail == 'form_2':
    #         template_id = self.env.ref('ev_hr_recruitment.template_hr_recruitment_send_mail_invite_work_form_2', False)
    #     elif self.type_mail == 'form_3':
    #         template_id = self.env.ref('ev_hr_recruitment.template_hr_recruitment_send_mail_invite_work_form_3', False)
    #
    #     self.body = template_id.body_html
    #     self.template_id = template_id.id



    # @api.multi
    # def send(self):
    #     for a in self.applicant_ids:
    #         if self.body:
    #             if self.type_mail == 'form_1':
    #                 template_id = self.env.ref('ev_hr_recruitment.template_hr_recruitment_send_mail_invite_work_form_1',
    #                                            False)
    #             elif self.type_mail == 'form_2':
    #                 template_id = self.env.ref('ev_hr_recruitment.template_hr_recruitment_send_mail_invite_work_form_2',
    #                                            False)
    #             elif self.type_mail == 'form_3':
    #                 template_id = self.env.ref('ev_hr_recruitment.template_hr_recruitment_send_mail_invite_work_form_3',
    #                                            False)
    #
    #             print  self.body
    #             template_id.body_html = self.body
    #             res = self.send_mail(template_id.id, a.applicant_email, a.id )
    #
    #         self._cr.execute(""" UPDATE hr_interview_line
    #                             SET is_sent_mail_invite_work = True
    #                             WHERE applicant_id = %s  and interview_id = %s """, (a.id,self.interview_id.id))
    #     return  res

    # def send_mail(self,cr, uid, template_id, applicant_email, applicant_id):
    #     mail_obj = self.pool('mail.recruitment')
    #     mail = mail_obj.create(cr, uid, {
    #         'email_to': applicant_email,
    #         'email_cc': 'odoo.izisolution@gmail.com',
    #         'subject': _('Giấy báo trúng tuyển'),
    #         'applicant_id': applicant_id,
    #     })
    #     a = self.pool('email.template').send_mail(cr, uid, template_id, mail,
    #                                               force_send=True)  # , force_send=True


