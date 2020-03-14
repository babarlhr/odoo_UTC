# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import except_orm, ValidationError
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import logging
_logger = logging.getLogger(__name__)



class hr_employee_going_on_business(models.Model):
    _name = 'hr.employee.going.on.business'
    _order = 'create_date DESC'

    name = fields.Char(string='Name', default='Going on business')
    employee_id = fields.Many2one('hr.employee', string='Employee')
    department_id = fields.Many2one('hr.department', string='Department')
    from_date = fields.Date(string="From date")
    to_date = fields.Date(string="To date")
    note = fields.Text(string="Note")
    state = fields.Selection([('draft', 'Draft'), ('wait_approval', 'Wait approval'), ('approved', 'Approved'), ('rejected', 'Rejected'), ('hr_confirm_cancel', 'HR confirm cancel')], default='draft')
    # thêm lý do nhân sự từ chối
    reason_cancel = fields.Text(string='Reason cancel')

    def unlink(self, cr, uid, ids, context=None):
        for line in self.browse(cr, uid, ids):
            if line.state not in ['draft', 'cancel']:
                raise except_orm('Thông báo !', 'Bạn chỉ được phép xóa những bản ghi ở trạng thái nháp !')
            elif line.create_uid.id != uid:
                raise except_orm('Thông báo !', 'Bạn chỉ được phép xóa những bản ghi mà bạn tạo !')
        return super(hr_employee_going_on_business, self).unlink(cr, uid, ids, context)

    @api.constrains('employee_id')
    def check_employee_id(self):
        #kiểm tra phòng ban
        if self.employee_id:
            if self.employee_id.department_id:
                self.department_id = self.employee_id.department_id.id
            else:
                raise ValidationError(_('Chưa cấu hình phòng ban cho nhân viên %s' % (self.employee_id.name_related)))

    @api.onchange('from_date', 'to_date')
    def onchange_from_date_to_date(self):
        if self.from_date and self.to_date and self.from_date > self.to_date:
            self.from_date = False
            self.to_date = False
            return {'warning': {
                    'title': _('Thông báo'),
                    'message': _('"Từ ngày" phải trước "Đến ngày". Vui lòng chọn lại!')
                }
            }

    @api.multi
    def send(self):
        obj_hr_employee_timesheet = self.env['hr.employee.timesheet']

        check_hr_employee_timesheet_is_closed = obj_hr_employee_timesheet.search([('employee_id', '=', self.employee_id.id),
                                                                  ('date', '>=', self.from_date),
                                                                  ('date', '<=', self.to_date),
                                                                  ('state', '<>', 'new')], limit=1)


        #kiểm tra đã được phân ca vào ngày đó chưa
        for single_date in self.daterange(datetime.strptime(self.from_date, '%Y-%m-%d'), datetime.strptime(self.to_date, '%Y-%m-%d')):
            single_date = single_date.strftime('%Y-%m-%d')
            employee_timesheet = obj_hr_employee_timesheet.search([('employee_id', '=', self.employee_id.id),
                                                                  ('date', '=', single_date)], limit=1)
            if not employee_timesheet:
                raise except_orm('Thông báo', _('Ngày ')
                                 + single_date
                                 + _(' không được phân ca.'))
            else:
                if employee_timesheet.shift_id.name == 'N':
                    raise except_orm('Thông báo', _('Ngày ')
                                     + single_date
                                     + _(' đang phân ca nghỉ nên không thể gửi!'))

        #kiểm tra bảng phân ca đã chốt chưa
        if check_hr_employee_timesheet_is_closed:
            raise except_orm('Thông báo', 'Đã chốt phân ca đến những ngày này không thể xin chế độ công tác!')

        #kiểm tra từ ngày nằm trong bản ghi đã xin
        query = '''select id from hr_employee_going_on_business where employee_id = %s
                    and ((from_date <= %s and to_date >= %s)or (from_date <= %s and to_date >= %s)or (from_date >= %s and to_date <= %s))
                    and state <> 'rejected'
                    and id != %s'''
        self._cr.execute(query, (
            self.employee_id.id, self.from_date, self.from_date, self.to_date, self.to_date, self.from_date,
            self.to_date, self.id))
        res = self._cr.dictfetchall()
        if res:
            employee_going_on_business = self.search([('id', '=', res[0]['id'])], limit=1)
            raise except_orm('Thông báo', _('Đã có đơn xin đi công tác cho nhân viên ')
                             + _(employee_going_on_business.employee_id.name_related)
                             + _(' từ ngày ') + _(employee_going_on_business.from_date)
                             + _(' đến ngày ') + _(employee_going_on_business.to_date))

        #kiểm tra phòng ban
        if self.employee_id.department_id:
            self.department_id = self.employee_id.department_id.id
        else:
            raise except_orm('Thông báo', 'Nhân viên không thuộc phòng ban nào!')

        self.state = 'wait_approval'

    @api.multi
    def approval(self):
        obj_hr_employee_timesheet = self.env['hr.employee.timesheet']
        # obj_hr_employee_shift = self.env['hr.employee.shift']

        hr_employee_timesheets = obj_hr_employee_timesheet.search([('employee_id', '=', self.employee_id.id),
                                                                  ('date', '>=', self.from_date),
                                                                  ('date', '<=', self.to_date)])
        # hr_employee_shift = obj_hr_employee_shift.search([('name', '=', 'CT')], limit=1)
        # if not hr_employee_shift: raise except_orm("Thông báo", "Chưa cấu hình ca công tác!")

        if hr_employee_timesheets:
            # for hr_employee_timesheet in hr_employee_timesheets:
            #     hr_employee_timesheet.write({
            #         'shift_id': hr_employee_shift.id
            #     })
            self.state = 'approved'
        else:
            raise except_orm('Thông báo', 'Chưa được phân ca trong khoảng thời gian này!')

    @api.multi
    def reject(self):
        view_id = self.env.ref('ev_hr_timesheet.view_hr_employee_going_on_business_reason_cancel_form').id
        return {
            'name': _('Lý do từ chối'),
            'view_mode': 'form',
            'view_type': 'form',
            'view_id': view_id,
            'res_id': self.id,
            'res_model': 'hr.employee.going.on.business',
            'type': 'ir.actions.act_window',
            'target': 'new',
        }

    @api.multi
    def action_cancel(self):
        #kiểm tra trưởng bộ phận:
        self.state = 'hr_confirm_cancel'
    @api.multi
    def action_hr_confirm_cancel(self):
        #kiểm tra trưởng bộ phận:
        view_id = self.env.ref('ev_hr_timesheet.view_hr_employee_going_on_business_reason_cancel_form').id
        return {
            'name': _('Lý do từ chối'),
            'view_mode': 'form',
            'view_type': 'form',
            'view_id': view_id,
            'res_id': self.id,
            'res_model': 'hr.employee.going.on.business',
            'type': 'ir.actions.act_window',
            'target': 'new',
        }

    @api.multi
    def confirm_reason_cancel(self):
        self.state = 'rejected'


    @api.model
    def create(self, vals):
        obj_hr_employee_timesheet = self.env['hr.employee.timesheet']
        new = super(hr_employee_going_on_business, self).create(vals)

        hr_employee_timesheet = obj_hr_employee_timesheet.search([('employee_id', '=', new.employee_id.id),
                                                                  ('date', '>=', new.from_date),
                                                                  ('date', '<=', new.to_date),
                                                                  ('state', '<>', 'new')], limit=1)
        if hr_employee_timesheet:
            raise except_orm('Thông báo', 'Đã chốt phân ca đến những ngày này không thể xin chế độ công tác!')

        #kiểm tra phòng ban
        if new.employee_id.department_id:
            new.department_id = new.employee_id.department_id.id
        else:
            raise except_orm('Thông báo', 'Nhân viên không thuộc phòng ban nào!')

        return new

    def daterange(self, from_date, to_date):
        for n in range(int((to_date - from_date).days) + 1):
            yield from_date + timedelta(n)
