# -*- coding: utf-8 -*-
from odoo import fields, models, api


class major(models.Model):
    _name = 'hr.major'

    name = fields.Char(string="Name")
    code = fields.Char(string="Code")
    description = fields.Text(string="Description")
