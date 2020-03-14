from odoo import models, fields, api, _

class level_employee_config(models.Model):
    _name = 'level.employee.config'


    name = fields.Char(string='Name')
    level = fields.Char(string='Level')
