# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

class training_rating(models.Model):
    _name = 'training.rating'


    name = fields.Char(string='Name')
    description = fields.Text(string='Description')
