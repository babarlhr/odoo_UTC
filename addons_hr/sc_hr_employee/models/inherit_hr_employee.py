# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
import logging
import time
from dateutil.relativedelta import relativedelta
from datetime import datetime
import random

_logger = logging.getLogger(__name__)


class sc_employee(models.Model):
    _inherit = 'hr.employee'
    _order = 'department_id'

    def update_new_code_employee(self):
        employee_obj = self.env['hr.employee'].sudo()
        dict = {
            'A': 10,
            'B': 11,
            'C': 12,
            'D': 13,
            'E': 14,
            'F': 15,
            'G': 16,
            'H': 17,
            'I': 18,
            'K': 19,
            'L': 20,
            'M': 21,
            'N': 22,
            'O': 23,
            'P': 24,
            'Q': 25,
            'R': 26,
            'S': 27,
            'T': 28,
            'U': 29,
            'V': 30,
            'X': 31,
            'Y': 32,
            'Z': 33,
            'a': 10,
            'b': 11,
            'c': 12,
            'd': 13,
            'e': 14,
            'f': 15,
            'g': 16,
            'h': 17,
            'i': 18,
            'k': 19,
            'l': 20,
            'm': 21,
            'n': 22,
            'o': 23,
            'p': 24,
            'q': 25,
            'r': 26,
            's': 27,
            't': 28,
            'u': 29,
            'v': 30,
            'x': 31,
            'y': 32,
            'z': 33,
        }
        query = """Select id, x_emp_code from hr_employee"""
        self._cr.execute(query)
        employees = self._cr.dictfetchall()
        if employees:
            for e in employees:
                if e['x_emp_code'] != '/':
                    employee = employee_obj.browse(e['id'])
                    code = e['x_emp_code']
                    prefix = code[0]
                    new_prefix = dict.get(prefix, False)
                    if new_prefix:
                        new_code = code.replace(prefix, str(new_prefix))
                    else:
                        new_code = code
                    employee.write({
                        'x_emp_code_new': new_code,
                    })
                _logger.error(e['x_emp_code'])
            return "done"

    def get_default_sequence(self):
        query = """
        SELECT MAX(sequence) _sequence From hr_employee
        """
        self._cr.execute(query)
        res = self._cr.dictfetchone()
        seq = res['_sequence'] if res['_sequence'] else 0
        if res:
            return seq + 1
        else:
            return 1

    def _defaut_x_em_code(self):
        return self.x_emp_code

    sequence = fields.Integer(string="Sequence", default=get_default_sequence)
    # sequence = fields.Integer(string="Sequence")
    x_emp_code = fields.Char(string=_('Code'), help=_('The employee code will be generated automatically'), select=True,
                             default='/', readonly=True)

    x_emp_code_new = fields.Char(string=_('Code New'), readonly=False, default=_defaut_x_em_code)
    # x_emp_code_new = fields.Char(string=_('Code New'), readonly=False)
    status = fields.Selection(selection=[('working', 'Working'),('leave', 'Leave'), ('retired', 'Retired')]
                              , default='working', required=True)
    address = fields.Char(string="Address", required=False)#Địa chỉ thường chú

    def _generate_emp_code(self):
        sequence = self.pool('ir.sequence').get(self.env.cr, self.env.uid, 'x_emp_code')
        x_emp_code = str(sequence)
        return x_emp_code

