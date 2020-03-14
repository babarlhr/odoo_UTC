# -*- coding: utf-8 -*-
from odoo import fields, models, api

class applicant_call_history(models.Model):
    _name = 'hr.applicant.call.history'

    @api.model
    def _default_recruitment_session_id(self):
        return self.env['hr.recruitment.session'].search([], limit=1, order='time_start_receive_resumes DESC')

    name = fields.Char(string='Name')
    note = fields.Text(string='Note', required=True)
    applicant_id = fields.Many2one('hr.applicant', string="Applicant", required=True)
    recruitment_session_id = fields.Many2one('hr.recruitment.session', string="Recruitment session", default=_default_recruitment_session_id, required=True)