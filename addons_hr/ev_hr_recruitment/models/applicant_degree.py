__author__ = 'dovietnga0909'
# -*- coding: utf-8 -*-
from odoo import fields, models, api


class applicant_degree(models.Model):
    _name = 'hr.applicant.degree'

    time = fields.Char(string="Time")
    school = fields.Char(string="School")
    major = fields.Char(string="Major")
    degree = fields.Char(string="Degree")
    level = fields.Char(string="Level")

    applicant_id = fields.Many2one('hr.applicant', string="Applicant", ondelete='cascade', required=True)
