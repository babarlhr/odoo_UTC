# -*- coding: utf-8 -*-
from odoo import fields, models, api, _
from odoo.exceptions import except_orm

STATUS_RECRUITMENT_SESSION_LINE_SELECTION = {
    ('process', 'Process'),
    ('enough', 'Enough'),
    ('not_enough', 'Not enough'),
    ('not_response', 'Not response')
}

ORIGIN_SELECTION = {
    ('recruitment_session', 'Recruitment session'),
    ('recruitment_request', 'Recruitment request'),
}

class recruitment_session_line(models.Model):
    _name = 'hr.recruitment.session.line'

    position_recruitment = fields.Char(string="Position recruitment")
    job_id = fields.Many2one('hr.job', string="Job Title", required=True)
    # job_position_id = fields.Many2one('hr.job.position', string="Job position", required=True)
    department_id = fields.Many2one('hr.department', string="Department", required=False)
    degree_id = fields.Many2one('hr.recruitment.degree', string="Degree")
    major_id = fields.Many2one('hr.major', string="major",)
    number_of_years_experience = fields.Integer(string="Number of years of experience", required=True)
    qty = fields.Integer(string="Quantity", required=True)
    description = fields.Text(string="Description")
    origin = fields.Selection(ORIGIN_SELECTION, default='recruitment_session', string="Origin")

    recruitment_session_id = fields.Many2one('hr.recruitment.session', string="recruitment session", ondelete='cascade')

    @api.constrains('qty',)
    def _check_qty(self):
        if self.qty <= 0:
            raise except_orm(_('Thông báo'), _('Số lượng nhập lớn hơn 0. Vui lòng nhập lại số lượng.'))