from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class mail_recruitment_popup(models.TransientModel):
    _name = 'mail.recruitment.popup'
    _inherit = ['mail.thread', 'mail.mail', 'mail.recruitment']

    # message_last_post = fields.Datetime(string="Last Message Date",
    #                                     help="Date of the last message posted on the record.")
    attachment_ids = fields.Many2many('ir.attachment', 'mail_recruitment_ir_attachment_rel', 'mail_recruitment_id', 'attachment_id', 'Attachments')
    interview_line_id = fields.One2many('hr.interview.line', string="interview_line_id")

    @api.multi
    def action_send_mail(self):

        template = self.env['ir.model.data'].sudo().get_object('ev_hr_recruitment', 'template_hr_recruitment_send_mail_invite_work_1')
        mail_obj = self.env['mail.recruitment.popup']
        mail = mail_obj.create({
            'email_to': 'dovietnga0909@gmail.com',
            'email_cc': 'superdreamptit@gmail.com',
            'subject': _('VMT GROUP_TH? M?I PH?NG V?N'),
        })

        for attachment_id in self.attachment_ids:
            query = """ INSERT INTO email_template_attachment_rel (email_template_id, attachment_id)  VALUES (%s,%s)"""
            self._cr.execute(query, (template.id, attachment_id.id))

        self.pool('email.template').send_mail(self._cr, 1, template.id, mail.id, force_send=True)  # , force_send=True