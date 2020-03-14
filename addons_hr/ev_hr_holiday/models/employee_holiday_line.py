# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import except_orm


class employee_holiday_line(models.Model):
    _name = 'hr.employee.holiday.line'

    employee_holiday_type_id = fields.Many2one('hr.employee.holiday.type', string="Holiday type", required=True)
    number_of_day = fields.Float(string="Number of day", default=1)
    employee_holiday_id = fields.Many2one('hr.employee.holiday', string="employee_holiday_id", ondelete='cascade')

    def unlink(self, cr, uid, ids, context=None):
        # for line in self.browse(cr, uid, ids):
        #     if line.state not in ['draft', 'cancel']:
        #         raise except_orm('Thông báo !', 'Bạn chỉ được phép xóa những bản ghi ở trạng thái nháp !')
        #     elif line.create_uid.id != uid:
        #         raise except_orm('Thông báo !', 'Bạn chỉ được phép xóa những bản ghi mà bạn tạo !')
        print("unlink: ")
        return super(employee_holiday_line, self).unlink(cr, uid, ids, context)


    @api.onchange('employee_holiday_type_id')
    def onchange_employee_holiday_type_id(self):
        if self.employee_holiday_type_id.category == 'is_unpaid_leave' or self.employee_holiday_type_id.category == 'is_employee_leave':
            self.number_of_day = 1
        else:
            self.number_of_day = self.employee_holiday_type_id.number_of_day

    @api.model
    def create(self, vals):
        new = super(employee_holiday_line, self).create(vals)
        if not new.number_of_day > 0:
            raise except_orm('Thông báo', 'Chưa nhập số ngày nghỉ phần chi tiết!')

        # check nhân viên đó đã có nghỉ phép quá số ngày chưa. có thì đưa lên thông báo
        if new.employee_holiday_type_id.category == 'is_employee_leave':
            cr = self._cr
            query = """SELECT (leave_day - used_day) remain_leave FROM hr_employee_leave a
                        WHERE a.employee_id = %s
                        AND a.from_date <= %s
                        AND a.to_date >= %s """
            cr.execute(query, (new.employee_holiday_id.employee_id.id, new.employee_holiday_id.from_date, new.employee_holiday_id.from_date))
            remain_leave = cr.dictfetchone()
            # tính luôn các đơn nháp
            holidays = self.env['hr.employee.holiday'].search([('employee_id', '=', new.employee_holiday_id.employee_id.id) ,
                                                               ('state', 'not in', ['cancel', 'done']),
                                                               ('id', '!=', new.employee_holiday_id.id),
                                                               ('from_date', '>=', str(new.employee_holiday_id.from_date)[0:4] + '-01-01' ),
                                                               ('to_date', '<=',str(new.employee_holiday_id.from_date)[0:4] + '-12-31' )])

            if remain_leave:
                remain_leave = remain_leave['remain_leave']
                if holidays:
                    for holiday in holidays:
                        remain_leave -= holiday.holidays

                if new.employee_holiday_id.holidays:
                    if new.employee_holiday_id.holidays > remain_leave:
                        raise except_orm('Thông báo', 'Quỹ phép đã được sử dụng hết! Vui lòng kiểm tra lại')
        return new