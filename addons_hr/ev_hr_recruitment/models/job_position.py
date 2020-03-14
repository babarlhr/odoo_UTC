# -*- coding: utf-8 -*-
from odoo import fields, models, api

class job_position(models.Model):
    _name = 'hr.job.position'

    name = fields.Char(string='Name')
    code = fields.Char(string='Code')
    description = fields.Text('Description')