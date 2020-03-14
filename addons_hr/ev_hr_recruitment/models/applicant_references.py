__author__ = 'dovietnga0909'
# -*- coding: utf-8 -*-
from odoo import fields, models, api


class applicant_references(models.Model):
    _name = 'hr.applicant.references'

    name = fields.Char(string="Name")
    relationship = fields.Char(string="Relationship")
    job_position = fields.Char(string="Job position")
    work_place = fields.Char(string="Work place")
    phone = fields.Char(string="Phone")
    email = fields.Char(string="Email")

    applicant_id = fields.Many2one('hr.applicant', string="Applicant", ondelete='cascade', required=True)
