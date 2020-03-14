# -*- coding: utf-8 -*-
from odoo import fields, models, api

class experience(models.Model):
    _name = "hr.experience"

    time = fields.Char(string="Time")
    name = fields.Char(string="Name")
    job_position = fields.Char(string="Job position")
    description = fields.Char(string="Description")
    pay_rate = fields.Char(string="Pay rate")
    reason_of_leaving = fields.Char(string="Reason of leaving")

    applicant_id = fields.Many2one('hr.applicant', string="Applicant", ondelete='cascade', required=True)