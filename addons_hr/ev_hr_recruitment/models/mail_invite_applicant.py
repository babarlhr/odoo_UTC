# -*- coding: utf-8 -*-
from odoo import fields, models, api

class mail_invite_applicant(models.TransientModel):
    _name = 'mail.invite.applicant'
    # partner_id = fields.Many2one('res.partner', string='Customer', required=True)
    # employee_id = fields.Many2one('res.users', string='Employee')
    # from_rank = fields.Many2one('customer.rank', string='From Rank')
    # to_rank = fields.Many2one('customer.rank', string='To rank')
    email_to = fields.Char(string='Email to')
    email_cc = fields.Char(string='Email cc')
    subject = fields.Char(string='Subject')
    applicant_name = fields.Char(string='Applicant name')
    # report_date = fields.Date(string='Date')
    # type = fields.Selection([('sent', 'Sent'), ('up', 'Up'), ('cancel', 'Cancel'),
    #                          ('exception', 'Exception'), ('extend', 'Extend'),('extend_up', 'Extend Up'),('extend_cancel', 'Extend Cancel')],
    #                         default='sent')


