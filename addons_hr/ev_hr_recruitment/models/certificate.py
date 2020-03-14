# -*- coding: utf-8 -*-
from odoo import fields, models, api

class certificate(models.Model):
    _name = 'hr.certificate'

    time = fields.Char(string="Time")
    name = fields.Char(string="Name")
    unit_allocation = fields.Char(string="Unit allocation")
    level = fields.Char(string="Level")

    applicant_id = fields.Many2one('hr.applicant', string="Applicant", ondelete='cascade', required=True)
