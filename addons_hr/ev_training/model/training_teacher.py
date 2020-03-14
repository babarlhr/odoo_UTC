from odoo import models, fields, api, _

class training_teacher(models.Model):
    _name = 'training.teacher'


    name = fields.Char(string='Name')
    employee_id = fields.Many2one('hr.employee',string='Teacher')

    @api.onchange('employee_id')
    def onchange_employee_id(self):
        if self.employee_id:
            self.name = self.employee_id.name



