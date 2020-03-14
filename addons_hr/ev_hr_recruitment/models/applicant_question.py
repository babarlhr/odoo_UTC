# -*- coding: utf-8 -*-
from datetime import datetime, date, timedelta
import requests
from odoo import fields, models, api, _

class hr_applicant_question(models.Model):
    _name = 'hr.applicant.question'


    name = fields.Char(string='Name')
    job_id = fields.Many2one('hr.job', string='Job group')
    attachment_ids = fields.Many2many('ir.attachment', string='Attachments')



