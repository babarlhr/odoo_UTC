# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import except_orm, ValidationError


class employee_holiday_type(models.Model):
    _name = 'hr.employee.holiday.type'

    name = fields.Char(string="Name", required=True)
    number_of_day = fields.Integer(string="Number of day")
    # timesheet_result_id = fields.Many2one('hr.timesheet.result', string="Timesheet result")
    category = fields.Selection([('is_special', 'Is special'), ('is_unpaid_leave', 'Is unpaid leave'), ('is_employee_leave', 'Is employee leave'), ('is_maternity', 'Is maternity'),('unpaid_leave_update_status','Unpaid leave update status')])

    @api.onchange('category')
    def onchange_category(self):
        obj_employee_holiday_type = self.env['hr.employee.holiday.type']
        if self.id and self.category:
            employee_holiday_type = obj_employee_holiday_type.search([('category', '=', self.category), ('id', '!=', self.id)])
        else:
            employee_holiday_type = obj_employee_holiday_type.search([('category', '=', self.category)])

        if employee_holiday_type and employee_holiday_type.category == 'is_employee_leave':
            raise except_orm(_('Thông báo'), _('Đã có kiểu nghỉ là Nghỉ phép, không thể thêm một nghỉ phép khác, vui lòng chọn lại!'))
        if employee_holiday_type and employee_holiday_type.category == 'is_unpaid_leave':
            raise except_orm(_('Thông báo'), _('Đã có kiểu nghỉ là Nghỉ không lương, không thể thêm một nghỉ không lương khác, vui lòng chọn lại!'))

    @api.constrains('category')
    def _check_category(self):
        obj_employee_holiday_type = self.env['hr.employee.holiday.type']
        if self.id and self.category:
            employee_holiday_type = obj_employee_holiday_type.search([('category', '=', self.category), ('id', '!=', self.id)])
        else:
            employee_holiday_type = obj_employee_holiday_type.search([('category', '=', self.category)])

        if employee_holiday_type.category == 'is_employee_leave':
            raise ValidationError("Đã có kiểu nghỉ là Nghỉ phép, không thể thêm một nghỉ phép khác, vui lòng chọn lại!")
        if employee_holiday_type.category == 'is_unpaid_leave':
            raise ValidationError("Đã có kiểu nghỉ là Nghỉ không lương, không thể thêm một nghỉ không lương khác, vui lòng chọn lại!")

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        cr = self._cr
        query = '''SELECT * FROM hr_employee_holiday_type a'''
        cr.execute(query)
        applicants = cr.dictfetchall()
        result = []
        for a in applicants:
            if a['category'] == 'is_unpaid_leave' or a['category'] == 'is_employee_leave':
                result.append([a['id'], a['name']])
            else:
                result.append([a['id'], a['name'] + '[' + str(a['number_of_day']) + ']'])
        res = result
        return res

    def name_get(self, cr, uid, ids, context=None):
        res = []
        for type in self.browse(cr, uid, ids, context=context):
            if type.category == 'is_unpaid_leave' or type.category == 'is_employee_leave':
                res.append([type.id, type.name])
            else:
                res.append([type.id, '[' + str(type.number_of_day) + ']' + type.name])
        return res