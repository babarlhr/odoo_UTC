# -*- coding: utf-8 -*-
from odoo import models, fields, api


class ev_hr_interview_questions(models.Model):
    _name = 'hr.interview.questions'

    name = fields.Char(string="Name")
    question = fields.Char(string="Question")
    department_id = fields.Many2one('hr.department',string="Department")
    description = fields.Text(string="Description")