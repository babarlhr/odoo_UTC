# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo import http
import odoo.addons.web.controllers.main as base_main
import logging


class sc_hr_department(models.Model):
    _inherit = 'hr.department'


    x_department_code = fields.Char(string=_("Department Code"), help=_('Enter the department code'), required=True)
    manager_id = fields.Many2one('hr.employee', string=_("Manager"), required=True)

    # def name_get(self, cr, uid, ids, context=None):
    #     res = []
    #     for department in self.browse(cr, uid, ids, context=context):
    #         code = department.x_department_code and department.x_department_code or ''
    #         res.append((department.id, '[' + code + '] ' + department.name))
    #     return res
