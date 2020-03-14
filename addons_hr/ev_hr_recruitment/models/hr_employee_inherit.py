# -*- coding: utf-8 -*-
from odoo import fields, models, api


class hr_employee_inherit(models.Model):
    _inherit = 'hr.employee'

    @api.multi
    def action_create_emp_from_applicant(self):
        applicant_id = self._context.get('applicant_id', False)
        if applicant_id:
            applicant_obj = self.env['hr.applicant']
            applicant = applicant_obj.search([('id', '=', applicant_id)])
            applicant.write({'status_applicant': 'is_employee'})
        return True
