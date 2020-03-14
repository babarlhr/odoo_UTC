# -*- coding: utf-8 -*-
from odoo import fields, models, api


class job(models.Model):
    _inherit = 'hr.job'
    _name = ''
    code = fields.Char(string='Code')
    description = fields.Text('Description')

    _sql_constraints = [
        ('code_uniq', 'unique(code)', 'Trùng code!'),
    ]
