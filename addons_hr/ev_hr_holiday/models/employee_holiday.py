# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.tools.translate import _
from lxml import etree
from dateutil.relativedelta import relativedelta
from odoo.exceptions import except_orm, ValidationError
from datetime import datetime, timedelta
import logging
_logger = logging.getLogger(__name__)



STATE_EMPLOYEE_HOLIDAY = [
    ('draft', 'Draft'),
    # ('wait_manager_approval', 'Wait manager approval'),
    # ('wait_hr_approval', 'Wait HR approval'),
    # ('wait_gd_approval', 'Wait GD approval'),
    ('done', 'Done'),
    # ('wait_manager_approval_cancel', 'Wait manager approval cancel'),
    # ('wait_hr_approval_cancel', 'Wait HR approval cancel'),
    ('cancel', 'Cancel'),
]


class employee_holiday(models.Model):
    _name = 'hr.employee.holiday'
    _order = 'id DESC'

    @api.depends('employee_holiday_line_ids')
    def _compute_detail_holiday(self):
        for r in self:
            query = '''SELECT (select string_agg(c.name || ' ' || b.number_of_day, ',' )
	from hr_employee_holiday_line b, hr_employee_holiday_type c
	WHERE a.id = b.employee_holiday_id and b.employee_holiday_type_id = c.id) as chitiet
from hr_employee_holiday a
WHERE a.id = %s '''
            self._cr.execute(query, (r.id,))
            detail_holiday = self._cr.dictfetchone()
            if detail_holiday:
                r.detail_holiday = detail_holiday['chitiet']



    name = fields.Char(string="Name", readonly=True, default='/', required=True)
    from_date = fields.Date(string="From date", required=True)
    to_date = fields.Date(string="To date", required=True)
    holidays = fields.Float(string="Holidays")
    employee_id = fields.Many2one('hr.employee', string="Employee", required=True)
    department_id = fields.Many2one('hr.department', string="Department")
    # work_time = fields.Float(string="Work time")
    # type_shift_haft_day = fields.Selection([('before', 'Before'), ('after', 'After')], string="Shift haft day")
    remaining_leave_day = fields.Char(string='Remaining leave day', compute='_compute_remaining_leave_day',
                                      readonly=True, store=True)
    detail_holiday = fields.Char(compute=_compute_detail_holiday)
    note = fields.Text(string="Note")
    employee_holiday_line_ids = fields.One2many('hr.employee.holiday.line', 'employee_holiday_id', string="Details")
    state = fields.Selection(STATE_EMPLOYEE_HOLIDAY, default='draft')
    # is_need_work_time = fields.Boolean(default=False)
    # is_haft_day = fields.Boolean(string="Is haft day")
    shift_id = fields.Many2one('hr.employee.shift', string='Shift')
    # shift_from_time = fields.Float(string='From time', related='shift_id.from_time', readonly=True)
    # shift_to_time = fields.Float(string='To time', related='shift_id.to_time', readonly=True)


    def unlink(self, cr, uid, ids, context=None):
        for line in self.browse(cr, uid, ids):
            if line.state not in ['draft', 'cancel']:
                raise except_orm('Thông báo !', 'Bạn chỉ được phép xóa những bản ghi ở trạng thái nháp !')
            elif line.create_uid.id != uid:
                raise except_orm('Thông báo !', 'Bạn chỉ được phép xóa những bản ghi mà bạn tạo !')
        return super(employee_holiday, self).unlink(cr, uid, ids, context)

    # @api.onchange('employee_id', 'from_date')
    # def onchange_employee_id_from_date(self):
    #     timesheet_obj = self.env['hr.employee.timesheet']
    #     if self.employee_id and self.from_date:
    #         timesheet = timesheet_obj.search(
    #             [('employee_id', '=', self.employee_id.id), ('date', '=', self.from_date)])
    #         if timesheet and len(timesheet) > 0:
    #             timesheet = timesheet[0]
    #             self.shift_id = timesheet.shift_id.id
    #         else:
    #             self.shift_id = False

    @api.constrains('employee_id')
    def check_employee_id(self):
        # kiểm tra phòng ban
        if self.employee_id:
            if self.employee_id.department_id:
                self.department_id = self.employee_id.department_id.id
            else:
                raise ValidationError(_('Chưa cấu hình phòng ban cho nhân viên %s' % (self.employee_id.name_related)))

    # @api.multi
    # def action_send(self):
    #
    #     # kiểm tra từ ngày không nằm trong bản ghi đã xin
    #     query = '''select id from hr_employee_holiday where employee_id = %s
    #                 and ((from_date <= %s and to_date >= %s)or (from_date <= %s and to_date >= %s)or (from_date >= %s and to_date <= %s))
    #                 and state <> 'cancel'
    #                 and id != %s'''
    #     self._cr.execute(query, (
    #         self.employee_id.id, self.from_date, self.from_date, self.to_date, self.to_date, self.from_date,
    #         self.to_date, self.id))
    #     res = self._cr.dictfetchall()
    #     if res:
    #         employee_holiday = self.search([('id', '=', res[0]['id'])], limit=1)
    #         raise except_orm('Thông báo', _('Đã có đơn xin nghỉ cho nhân viên ')
    #                          + _(employee_holiday.employee_id.name_related)
    #                          + _(' từ ngày ') + _(employee_holiday.from_date)
    #                          + _(' đến ngày ') + _(employee_holiday.to_date))
    #
    #     # obj_hr_employee_timesheet = self.env['hr.employee.timesheet']
    #     obj_hr_employee_leave = self.env['hr.employee.leave']
    #     hr_employee_timesheet_to_date = obj_hr_employee_timesheet.search(
    #         [('employee_id', '=', self.employee_id.id), ('date', '=', self.to_date)], limit=1)
    #     hr_employee_timesheet_close = obj_hr_employee_timesheet.search(
    #         [('employee_id', '=', self.employee_id.id), ('date', '>=', self.from_date), ('date', '<=', self.to_date),
    #          ('state', '<>', 'new')], limit=1)
    #     hr_employee_timesheet_all = obj_hr_employee_timesheet.search(
    #         [('employee_id', '=', self.employee_id.id), ('date', '>=', self.from_date), ('date', '<=', self.to_date),
    #          ('shift_id.name', '=', 'N')])
    #     if self.holidays <= 0:
    #         raise except_orm(_('Thông báo'), _('Số ngày nghỉ phải lớn hơn 0!.'))
    #
    #     number_of_day = 0
    #     number_of_leave_day = 0
    #     for employee_holiday_line_id in self.employee_holiday_line_ids:
    #         print("employee_holiday_line_id.number_of_day: " + str(employee_holiday_line_id.number_of_day))
    #         number_of_day += employee_holiday_line_id.number_of_day
    #
    #         # if employee_holiday_line_id.employee_holiday_type_id.category == 'is_employee_leave' or employee_holiday_line_id.employee_holiday_type_id.category == 'is_unpaid_leave':
    #         if employee_holiday_line_id.employee_holiday_type_id.category == 'is_employee_leave':
    #             number_of_leave_day += employee_holiday_line_id.number_of_day
    #
    #     if number_of_day != self.holidays:
    #         raise except_orm(_('Thông báo'), _('Số ngày bạn chọn phải bằng số ngày xin nghỉ, vui lòng chọn lại'))
    #
    #
    #     number_of_unpaid_leave_day = 0
    #     if self.employee_holiday_line_ids:
    #         for employee_holiday_line_id in self.employee_holiday_line_ids:
    #             if employee_holiday_line_id.employee_holiday_type_id.category == 'is_employee_leave':
    #                 hr_employee_leave = obj_hr_employee_leave.search([('employee_id', '=', self.employee_id.id),
    #                                                                   ('from_date', '<=', self.from_date),
    #                                                                   ('to_date', '>=', self.from_date)])
    #                 if hr_employee_leave:
    #                     if int(self.from_date[5:7]) >= 4:
    #                         leave_day = hr_employee_leave.leave_day
    #                         used_day = hr_employee_leave.used_day
    #                         if number_of_leave_day > (leave_day - used_day):
    #                             raise except_orm('Thông báo',
    #                                              'Số ngày xin nghỉ phép lớn hơn số ngày nghỉ phép còn lại, Vui lòng chọn lại!.')
    #                     else:
    #                         leave_day = hr_employee_leave.leave_day
    #                         used_day = hr_employee_leave.used_day
    #                         rest_leave_day = hr_employee_leave.rest_leave_day
    #                         leave_day_last_year = hr_employee_leave.leave_day_last_year
    #
    #                         if number_of_leave_day > (leave_day - used_day) + (rest_leave_day - leave_day_last_year):
    #                             raise except_orm('Thông báo',
    #                                              'Số ngày xin nghỉ phép lớn hơn số ngày nghỉ phép còn lại, Vui lòng chọn lại!.')
    #                 else:
    #                     raise except_orm('Thông báo', 'Nhân viên chưa có quỹ nghỉ phép')
    #                 # if hr_employee_leave:
    #                 #     leave_day = hr_employee_leave.leave_day
    #                 #     used_day = hr_employee_leave.used_day
    #                 #     if number_of_leave_day > (leave_day - used_day):
    #                 #         raise except_orm('Thông báo',
    #                 #                          'Số ngày xin nghỉ phép lớn hơn số ngày nghỉ phép còn lại, Vui lòng chọn lại!.')
    #                 # else:
    #                 #     raise except_orm('Thông báo', 'Nhân viên chưa có quỹ nghỉ phép')
    #                 number_of_leave_day += employee_holiday_line_id.number_of_day
    #             if employee_holiday_line_id.employee_holiday_type_id.category == 'is_unpaid_leave':
    #                 number_of_unpaid_leave_day += employee_holiday_line_id.number_of_day
    #             for single_date in self.daterange(datetime.strptime(self.from_date, '%Y-%m-%d'),
    #                                               datetime.strptime(self.to_date, '%Y-%m-%d')):
    #                 single_date = single_date.strftime('%Y-%m-%d')
    #                 timesheet_check = obj_hr_employee_timesheet.search(
    #                     [('employee_id', '=', self.employee_id.id), ('date', '=', single_date)])
    #                 if not timesheet_check or not timesheet_check.shift_id:
    #                     if self.employee_holiday_line_ids:
    #                 # for a in self.employee_holiday_line_ids:
    #                 #     if a.employee_holiday_type_id.category == 'is_maternity':
    #                 #         print  'done'
    #                 #     else:
    #                         for employee_holiday_line_id in self.employee_holiday_line_ids:
    #                             if employee_holiday_line_id.employee_holiday_type_id.update_status_employee is True:
    #                                 if employee_holiday_line_id.employee_holiday_type_id.category in (
    #                                 'is_maternity', 'unpaid_leave_update_status'):
    #                                     return True
    #                             else:
    #                                 raise except_orm(_('Thông báo'),
    #                                                  _('Ngày bạn đi làm trở lại chưa được phân ca!.'))
    #     # check bản ghi chi tiết
    #     if not self.employee_holiday_line_ids:
    #         raise except_orm(_('Thông báo'), _('Phải có bản ghi chi tiết!.'))



    # @api.onchange('from_date', 'to_date', 'employee_id')
    # def onchange_from_date_to_date_employee(self):
    #     user_obj = self.env['res.users']
    #     timesheet_obj = self.env['hr.employee.timesheet']
    #     # for s in self:
    #     if self.is_haft_day:
    #         self.to_date = self.from_date
    #     elif self.from_date and self.to_date and self.employee_id:
    #         number_day_from_date_to_date = (datetime.strptime(self.to_date, '%Y-%m-%d') - datetime.strptime(
    #             self.from_date, '%Y-%m-%d')).days + 1
    #         self.holidays = number_day_from_date_to_date
    #
    #         timesheet = timesheet_obj.search([('employee_id', '=', self.employee_id.id),('date', '>=', self.from_date), ('date', '<=', self.to_date)])
    #         if timesheet and len(timesheet) >=1:
    #             for i in timesheet:
    #                 if i.shift_id.name == 'H':
    #                     self.holidays = self.holidays - 0.5
    #                 elif i.shift_id.name == 'N':
    #                     self.holidays = self.holidays - 1
    #
    #     else:
    #         self.holidays = 0

    @api.depends('employee_id', 'from_date', 'employee_holiday_line_ids')
    def _compute_remaining_leave_day(self):
        for s in self:
            is_employee_leave = False
            if s.employee_id and s.from_date and len(s.employee_holiday_line_ids) > 0:
                for employee_holiday_line_id in s.employee_holiday_line_ids:
                    if employee_holiday_line_id.employee_holiday_type_id.category == 'is_employee_leave':
                        is_employee_leave = True

                if is_employee_leave:
                    cr = self._cr
                    query = """SELECT * FROM hr_employee_leave a
                                WHERE a.employee_id = %s
                                AND a.from_date <= %s
                                AND a.to_date >= %s """
                    cr.execute(query, (s.employee_id.id, s.from_date, s.from_date))
                    employee_leave_ids = cr.dictfetchall()
                    if employee_leave_ids:
                        s.remaining_leave_day = str(
                            employee_leave_ids[0]['leave_day'] - employee_leave_ids[0]['used_day']) + '/' + str(
                            employee_leave_ids[0]['leave_day'])
                        if datetime.strptime(s.from_date, '%Y-%m-%d').month < 4:
                            s.remaining_leave_day += _(' (Số ngày phép năm trước: ') + str(
                                employee_leave_ids[0]['leave_day_last_year']) + '/' + str(
                                employee_leave_ids[0]['rest_leave_day']) + ')'

                    else:
                        s.employee_id = False
                        raise except_orm(_('Thông báo'), _('Chưa cấu hình nghỉ phép cho nhân viên này!.'))
                else:
                    s.remaining_leave_day = str(0) + '/' + str(0)

    @api.onchange('employee_holiday_line_ids')
    def onchange_employee_holiday_line_ids(self):
        number_of_day = 0
        number_of_leave_day = 0
        for employee_holiday_line_id in self.employee_holiday_line_ids:
            number_of_day += employee_holiday_line_id.number_of_day
            if employee_holiday_line_id.employee_holiday_type_id.category == 'is_employee_leave' or employee_holiday_line_id.employee_holiday_type_id.category == 'is_unpaid_leave':
                number_of_leave_day += employee_holiday_line_id.number_of_day

        if number_of_day != self.holidays:
            return {'warning': {
                'title': _('Thông báo'),
                'message': _('Số ngày bạn chọn phải bằng số ngày xin nghỉ, vui lòng chọn lại!.')
            }
            }

        if number_of_leave_day > self.remaining_leave_day:
            return {'warning': {
                'title': _('Thông báo'),
                'message': _('Số ngày xin nghỉ phép lớn hơn số ngày nghỉ phép còn lại, Vui lòng chọn lại!.')
            }
            }

    @api.constrains('employee_holiday_line_ids')
    def _check_employee_holiday_line_ids(self):
        number_of_day = 0
        number_of_leave_day = 0
        for employee_holiday_line_id in self.employee_holiday_line_ids:
            number_of_day += employee_holiday_line_id.number_of_day
            if employee_holiday_line_id.employee_holiday_type_id.category == 'is_employee_leave' or employee_holiday_line_id.employee_holiday_type_id.category == 'is_unpaid_leave':
                number_of_leave_day += employee_holiday_line_id.number_of_day

        if number_of_day != self.holidays:
            raise ValidationError("Số ngày bạn chọn phải bằng số ngày xin nghỉ, vui lòng chọn lại.")

        if number_of_leave_day > self.remaining_leave_day:
            raise ValidationError("Số ngày xin nghỉ phép lớn hơn số ngày nghỉ phép còn lại, Vui lòng chọn lại!.")

    @api.onchange('from_date')
    def onchange_from_date(self):
        if self.to_date and self.from_date > self.to_date:
            self.from_date = False
            return {'warning': {
                'title': _('Thông báo'),
                'message': _('Ngày kết thúc nghỉ phải sau ngày bắt đầu nghỉ, vui lòng chọn lại.')
            }
            }


    @api.onchange('to_date')
    def onchange_to_date(self):
        if self.to_date and self.from_date and self.from_date > self.to_date:
            self.to_date = False
            return {'warning': {
                'title': _('Thông báo'),
                'message': _('Ngày kết thúc nghỉ phải sau ngày bắt đầu nghỉ, vui lòng chọn lại.')
            }
            }

    @api.model
    def create(self, vals):
        vals['name'] = self.pool.get('ir.sequence').next_by_code(self.env.cr, self.env.uid, 'hr_holiday_name_seq')
        res = super(employee_holiday, self).create(vals)

        return res

    def daterange(self, from_date, to_date):
        for n in range(int((to_date - from_date).days) + 1):
            yield from_date + timedelta(n)

