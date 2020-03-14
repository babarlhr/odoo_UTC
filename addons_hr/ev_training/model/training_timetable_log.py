# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import except_orm


class training_timetable_log(models.Model):
    _name = 'training.timetable.log'

    session_id = fields.Many2one('training.session', string='Session')
    major_id = fields.Many2one('training.major', string='Major')
    time = fields.Float(string='Time')
    date = fields.Date(string='Date')
