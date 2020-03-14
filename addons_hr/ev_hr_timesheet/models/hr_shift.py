# -*- coding: utf-8 -*-
import logging
from lxml import etree

from odoo import models, fields, api, _
from datetime import datetime
from dateutil.relativedelta import relativedelta
from odoo.exceptions import except_orm, ValidationError
from dateutil.relativedelta import relativedelta
import base64
import xlrd

_logger = logging.getLogger(__name__)


class ev_hr_shift(models.Model):
    _name = 'hr.employee.shift'

    name = fields.Char(string='Name')
    break_time = fields.Float(string='Break time')
    from_time = fields.Float(string='Time from')
    to_time = fields.Float(string='Time to')
    description = fields.Text(string='Desc')
    standard_time = fields.Float(string='Standard time')
    overtime_rate = fields.Float(string='Overtime rate')
    department_ids = fields.Many2many('hr.department', string='Departments')
    shift_standard_ids = fields.One2many('hr.employee.shift.standard', 'shift_id', string='Standard details')
    _sql_constraints = [
        ('name_unique', 'unique(name)', 'Tên ca bị trùng, vui lòng nhập tên khác!'),
    ]

    @api.constrains('shift_standard_ids')
    def _constraint_shift_standard_ids(self):
        if self.shift_standard_ids:
            for shift_standard_id in self.shift_standard_ids:
                if not shift_standard_id.job_id or shift_standard_id.standard_time <= 0:
                    shift_standard_id.unlink()

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        name = name.upper()
        context = self._context
        cr = self._cr
        uid = self._uid
        operator = '='
        print("_context: " + str(context))
        if 'department_id' in context:
            if not (uid == 1):
                query = "SELECT hr_employee_shift_id FROM hr_department_hr_employee_shift_rel WHERE hr_department_id = %s"
                cr.execute(query, (context['department_id'], ))
                res = cr.fetchall()
                print("res: " + str(res))
                if res:
                    args += [['id', 'in', res]]
                    # return self.sudo().search_read(fields=['id', 'name'], domain=[('id', 'in', res), ('name', '=', name)])
                else:
                    args += [['id', '=', 0]]
            #         return self.sudo().search_read(fields=['id', 'name'], domain=[('id', '=', 0)])
            # else:
            #     return super(ev_hr_shift, self).name_search(cr, uid, name, args, operator=operator, context=context, limit=limit)
        # else:
        print("_args: " + str(args))
        print("_operator3: " + str(operator))
        return super(ev_hr_shift, self).name_search(name, args, operator=operator, limit=limit)

    def get_shift_by_department(self, cr, uid, department_id=0):
        arr_employee_shifts = []
        obj_employee_shift = self.pool.get('hr.employee.shift')
        employee_shift_ids = obj_employee_shift.search(cr, uid, [('department_ids', 'child_of', department_id)])
        employee_shifts = obj_employee_shift.browse(cr, uid, employee_shift_ids)
        for employee_shift in employee_shifts:
            arr_employee_shifts.append(employee_shift.name)
        print("arr_employee_shifts: " + str(arr_employee_shifts))
        return arr_employee_shifts

    def get_standard(self, employee_id):
        # obj_employee = self.env['hr.employee']
        # employee = obj_employee.search([('id', '=', employee_id)], limit=1)
        # if not employee: raise except_orm('Thông báo', 'Nhân viên có id ' + str(employee_id) + ' không tồn tại khi lấy giờ công chuẩn. Vui lòng liên hệ Admin để được giải quyết.')

        if self.shift_standard_ids:
            for shift_standard_id in self.shift_standard_ids:
                if shift_standard_id.job_id.id == employee_id.job_id.id:
                    return shift_standard_id.standard_time
            return self.standard_time
        else:
            return self.standard_time


class hr_shift_standard(models.Model):
    _name = 'hr.employee.shift.standard'

    job_id = fields.Many2one('hr.job', string='Job')
    standard_time = fields.Float(string='Standard time')

    shift_id = fields.Many2one('hr.employee.shift', string='Shift')

map_day = {
    'day_1': 1,
    'day_2': 2,
    'day_3': 3,
    'day_4': 4,
    'day_5': 5,
    'day_6': 6,
    'day_7': 7,
    'day_8': 8,
    'day_9': 9,
    'day_10': 10,
    'day_11': 11,
    'day_12': 12,
    'day_13': 13,
    'day_14': 14,
    'day_15': 15,
    'day_16': 16,
    'day_17': 17,
    'day_18': 18,
    'day_19': 19,
    'day_20': 20,
    'day_21': 21,
    'day_22': 22,
    'day_23': 23,
    'day_24': 24,
    'day_25': 25,
    'day_26': 26,
    'day_27': 27,
    'day_28': 28,
    'day_29': 29,
    'day_30': 30,
    'day_31': 31,
}

class ev_hr_shift_assign(models.Model):
    _name = 'hr.shift.assign'
    _order = 'department_id asc, create_date DESC'

    def _get_default_department(self):
        employee_id = self.get_employee_from_user()
        obj_hr_employee = self.env['hr.employee']
        if employee_id:
            hr_employee = obj_hr_employee.search([('id', '=', employee_id)])
            # department = self.env['hr.department'].search([('manager_id', '=', employee_id)])
            # if department and len(department) > 0:
            return hr_employee.department_id
        else:
            return False

    # def _get_domain_department(self):
    #     employee_id = self.get_employee_from_user()
    #     obj_hr_employee = self.env['hr.employee']
    #     if employee_id:
    #         departments = self.env['hr.department'].search([('manager_id', '=', employee_id)])
    #         hr_employee = obj_hr_employee.search([('id', '=', employee_id)])
    #         ids = []
    #         ids.append(hr_employee.department_id.id)
    #         if departments and len(departments) > 0:
    #             ids = list(department.id for department in departments)
    #             ids.append(hr_employee.department_id.id)
    #         print("ids: " + str(ids))
    #         return [('id', 'in', ids)]
    #         # else:
    #         #     return [('id', 'in', ids)]


    def _compute_employee_shift(self):
        print("employee_shifts: ")
        # for s in self:
        if self.department_id:
            obj_employee_shift = self.env['hr.employee.shift']
            employee_shifts = obj_employee_shift.search([('department_ids', 'child_of', self.department_id.id)])
            self.employee_shift_ids = employee_shifts

    name = fields.Char(string='Name', default='Init employee shift')
    detail_ids = fields.One2many('hr.shift.assign.detail', 'init_id')
    period_id = fields.Many2one('account.period', string='Month', required=True)
    department_id = fields.Many2one('hr.department', string='Department', default=_get_default_department, required=True)
    # department_name = fields.Char(related='department_id.x_department_code', string='Department name', readonly=True)
    file_upload = fields.Binary(string='File upload')
    file_name = fields.Char(string='File name')
    state = fields.Selection(
        [('init', 'Init'), ('draft', 'Draft'), ('wait_approval', 'Wait approval'), ('approved', 'Approved'),
         ('done', 'Done'), ('cancel', 'Cancel')], default='init')

    # from_date vs to_date dùng để tách chốt bảng phân ca theo giai đoạn. đừng có thắc mắc
    from_date = fields.Integer(string='From date')
    to_date = fields.Integer(string='To date')
    close_timesheet_date = fields.Integer(string='Close timesheet date', default=0)
    employee_shift_ids = fields.One2many('hr.employee.shift', string='Shift', compute=_compute_employee_shift)
    random_number = fields.Integer(string='Random number')
    random_number_1 = fields.Float(string='Random number 1')
    close_timesheet_type = fields.Selection([('department', 'Department'), ('department_timesheet', 'Department timesheet')], default='department_timesheet', string='Close timesheet type')



    @api.multi
    def write(self, values):
        # res = super(ev_hr_shift_assign, self).write(values)
        # random = randint(0, 9999999)
        # print random
        # self.random_number = random
        values.update({'random_number': self.random_number + 1})
        res = super(ev_hr_shift_assign, self).write(values)
        return res

    # def fields_view_get(self, cr, uid, view_id=None, view_type='form',
    #                     context=None, toolbar=False, submenu=False):
    #     if context is None:
    #         context = {}
    #     res = super(ev_hr_shift_assign,self).fields_view_get(cr, uid, view_id, view_type, context, toolbar, submenu)
    #     mod_obj = self.pool.get('ir.model.data')
    #     obj_res_users = self.pool.get('res.users')
    #     dummy, except_view_id = tuple(mod_obj.get_object_reference(cr, uid, 'ev_hr_timesheet', "hr_shift_assign_form_view"))
    #     print("view_type: " + str(view_type))
    #     if view_type == 'form':
    #         doc = etree.XML(res['arch'])
    #         # print(doc)
    #         # print("obj_hr_attendance_exception.employee_id: " + str(obj_hr_attendance_exception._ids))
    #         # print("uid: " + str(uid))
    #         # if obj_hr_attendance_exception.create_uid != uid:
    #         is_hr_manager = obj_res_users.has_group(cr, uid, 'base.group_hr_user')
    #         if is_hr_manager:
    #             for node in doc.xpath("//button[@name='revoke']"):
    #                 node.set('string', _("Yêu cầu chỉnh sửa lại"))
    #
    #         xarch, xfields = self._view_look_dom_arch(cr, uid, doc, except_view_id, context=context)
    #         res['arch'] = xarch
    #         res['fields'] = xfields
    #     return res


    def unlink(self, cr, uid, ids, context=None):
        for line in self.browse(cr, uid, ids):
            if line.state not in ['init', 'draft', 'cancel']:
                raise except_orm('Thông báo !', 'Bạn chỉ được phép xóa những bản ghi ở trạng thái nháp hoặc hủy !')
            elif line.create_uid.id != uid:
                raise except_orm('Thông báo !', 'Bạn chỉ được phép xóa những bản ghi mà bạn tạo !')
        return super(ev_hr_shift_assign, self).unlink(cr, uid, ids, context)

    @api.multi
    def send(self):
        user_obj = self.env['res.users']
        is_hr_manager = user_obj.has_group('base.group_hr_user')

        now = datetime.now().today()
        date = datetime.strftime(now, '%Y-%m-%d')
        today = datetime.strptime(date, '%Y-%m-%d')
        self_date = datetime.strptime(self.period_id.date_start, '%Y-%m-%d')
        if is_hr_manager:
            print(111)
        else:
            if self.create_uid.id != self._uid:
                raise except_orm('Thông báo', 'Chỉ gửi những bản ghi do bạn tạo ra!')

            if int(str(today)[5:7]) == int(str(self_date)[5:7]):
                if (int(str(today)[8:10]) - int(str(self_date)[8:10])) > 3 and int(str(today)[8:10]) > int(str(self_date)[8:10]):
                    raise except_orm('Thông báo', 'Chỉ được phép phân ca làm việc trước 3 ngày so với ngày hiện tại')
            else:
                if int(str(self_date)[5:7]) < int(str(today)[5:7]):
                    if int(str(today)[8:10]) not in (1, 28, 29, 30,31):
                        raise except_orm('Thông báo', 'Khi phân ca cho tháng trong quá khứ!  Phải gửi trước ngày mùng 2 của tháng tiếp theo!')
                if self.create_uid.id != self._uid:
                    raise except_orm('Thông báo', 'Chỉ gửi những bản ghi do bạn tạo ra!')
        self.state = 'wait_approval'

    @api.multi
    def refresh(self):
        if self.state == 'draft':
            shift_obj = self.env['hr.employee.shift']
            TS_shift = shift_obj.search([('name', '=', 'TS')])
            obj_employee_holiday_ts = self.env['hr.employee.holiday']
            # self.state = 'init'
            employee_obj = self.env['hr.employee']
            current_details = {}
            for d in self.detail_ids:
                data = {
                    'employee_id': d.employee_id.id,
                    'day_1': d.day_1.id,
                    'day_2': d.day_2.id,
                    'day_3': d.day_3.id,
                    'day_4': d.day_4.id,
                    'day_5': d.day_5.id,
                    'day_6': d.day_6.id,
                    'day_7': d.day_7.id,
                    'day_8': d.day_8.id,
                    'day_9': d.day_9.id,
                    'day_10': d.day_10.id,
                    'day_11': d.day_11.id,
                    'day_12': d.day_12.id,
                    'day_13': d.day_13.id,
                    'day_14': d.day_14.id,
                    'day_15': d.day_15.id,
                    'day_16': d.day_16.id,
                    'day_17': d.day_17.id,
                    'day_18': d.day_18.id,
                    'day_19': d.day_19.id,
                    'day_20': d.day_20.id,
                    'day_21': d.day_21.id,
                    'day_22': d.day_22.id,
                    'day_23': d.day_23.id,
                    'day_24': d.day_24.id,
                    'day_25': d.day_25.id,
                    'day_26': d.day_26.id,
                    'day_27': d.day_27.id,
                    'day_28': d.day_28.id,
                    'day_29': d.day_29.id,
                    'day_30': d.day_30.id,
                    'day_31': d.day_31.id,
                }

                current_details.update({d.employee_id.id: data})
            self.detail_ids.unlink()
            employees = employee_obj.search([('department_timesheet_id', '=', self.department_id.id), ('status', 'in', ('working', 'maternity_leave'))],
                                            order='department_id desc, is_lead_team desc, job_priority, job_id, x_join_date asc')
            if employees and len(employees) > 0:
                for employee in employees:
                    args = {
                        'init_id': self.id,
                    }
                    old_employee_data = current_details.get(employee.id, False)
                    if old_employee_data:
                        args.update(old_employee_data)
                    else:
                        H_shift = shift_obj.search([('name', '=', 'H')])
                        N_shift = shift_obj.search([('name', '=', 'N')])
                        end_date = datetime.strptime(self.period_id.date_stop, '%Y-%m-%d')
                        args.update({'employee_id': employee.id})
                        if employee.default_shift_id:
                            if employee.default_shift_id.name != 'X':
                                for key, value in map_day.iteritems():
                                    if value <= end_date.day:
                                        args.update({key: employee.default_shift_id.id})
                            else:
                                for key_hc, value_hc in map_day.iteritems():
                                    if value_hc <= end_date.day:
                                        month = end_date.strftime('%Y-%m')
                                        check_day_str = month + '-' + str(value_hc)
                                        check_day = datetime.strptime(check_day_str, '%Y-%m-%d')
                                        weekday = check_day.weekday()
                                        if weekday == 5:  # Saturday
                                            args.update({key_hc: H_shift.id})
                                        elif weekday == 6:  # Sunday
                                            args.update({key_hc: N_shift.id})
                                        else:
                                            args.update({key_hc: employee.default_shift_id.id})

                        else:
                            for key, value in map_day.iteritems():
                                check_ts = False
                                if int(self.period_id.date_stop[8:10]) >= value:
                                    day_check_holiday = str(self.period_id.date_start[0:7]) + '-' + str(value)
                                    search_hr_employee_holiday_date = obj_employee_holiday_ts.search(
                                        [('state', '=', 'done'), ('employee_id', '=', employee.id),
                                         ('from_date', '<=', day_check_holiday), ('to_date', '>=', day_check_holiday)])
                                    if search_hr_employee_holiday_date:
                                        if len(search_hr_employee_holiday_date.employee_holiday_line_ids) >= 1:
                                            for a in search_hr_employee_holiday_date.employee_holiday_line_ids:
                                                if a.employee_holiday_type_id.category == 'is_maternity':
                                                    check_ts = True
                                if check_ts is True:
                                    args.update({key: TS_shift.id})
                        self.detail_ids.create(args)
                    self.detail_ids.create(args)
                    self._cr.execute(
                        "SELECT day_30,day_31,day_18,day_19,day_14,day_15,day_16,day_17,day_10,day_11,day_12,day_13,day_8,day_9,day_2,day_3,"
                        "day_1,day_6,day_7,day_4,day_5,day_21,day_20,day_23,day_22,day_25,day_24,day_27,day_26,day_29,day_28 "
                        "FROM hr_shift_assign_detail WHERE init_id = %s and employee_id = %s ",
                        (self.id,employee.id,))
                    hr_shift_assign_detail = self._cr.dictfetchone()

                    for key_hr_shift_assign_detail, value_hr_shift_assign_detail in hr_shift_assign_detail.iteritems():
                        date = key_hr_shift_assign_detail.split('_')[1]
                        check_ts = False
                        day_check_holiday = False
                        if int(date) <= int(str(self.period_id.date_stop)[8:10]):
                            day_check_holiday = str(self.period_id.date_start[0:7]) + '-' + str(date)
                        search_hr_employee_holiday_date = obj_employee_holiday_ts.search(
                            [('state', '=', 'done'), ('employee_id', '=', employee.id),
                             ('from_date', '<=', day_check_holiday), ('to_date', '>=', day_check_holiday)])
                        if search_hr_employee_holiday_date:
                            if len(search_hr_employee_holiday_date.employee_holiday_line_ids) >= 1:
                                for a in search_hr_employee_holiday_date.employee_holiday_line_ids:
                                    if a.employee_holiday_type_id.category == 'is_maternity':
                                        check_ts = True
                        if check_ts is True:
                            query = 'update hr_shift_assign_detail set ' + key_hr_shift_assign_detail + ' = %s where employee_id = %s and init_id = %s '

                            self._cr.execute(query, (TS_shift.id, employee.id, self.id,))


        else:
            raise except_orm('Chỉ làm mới được những bản ghi ở trạng thái nháp!')

    @api.multi
    def revoke(self):
        if self.state == 'wait_approval':
            self.state = 'draft'
        else:
            raise except_orm('Thông báo', 'Chỉ thu hồi được phân ca làm việc ở trạng thái chờ phê duyệt!')

    @api.multi
    def approval(self):
        if self.state == 'wait_approval':
            obj_hr_maternity_leave_history = self.env['hr.maternity.leave.history']
            obj_employee_timesheet = self.env['hr.employee.timesheet']
            obj_standard_time_config = self.env['hr.standard.time.config']
            obj_employee = self.env['hr.employee']
            end_date = datetime.strptime(self.period_id.date_stop, '%Y-%m-%d')
            month = end_date.strftime('%Y-%m')
            query = "Select * from hr_shift_assign_detail where init_id = %s"
            self._cr.execute(query, (self.id,))
            res = self._cr.dictfetchall()
            if res and len(res) > 0:
                priority = 0
                for r in res:
                    employee_id = obj_employee.search([('id', '=', r['employee_id'])], limit=1)

                    if not employee_id.department_timesheet_id.category:
                        raise except_orm('Thông báo', 'Phòng ban chấm công [%s] %s của nhân viên [%s] %s chưa được cấu hình khối.' % (employee_id.department_timesheet_id.x_department_code, employee_id.department_timesheet_id.name, employee_id.x_emp_code, employee_id.name_related, ))
                    if not employee_id.job_id:
                        raise except_orm('Thông báo', 'Nhân viên [%s] %s chưa được cấu hình chức danh.' % (employee_id.x_emp_code, employee_id.name_related, ))

                    #tìm giờ công chuẩn
                    standard_time_config = obj_standard_time_config.search([('department_category', '=', employee_id.department_timesheet_id.category and employee_id.department_timesheet_id.category or ''), ('job_id', '=', employee_id.job_id and employee_id.job_id.id or 0)], limit=1)
                    #nếu ko tìm thấy, dùng ko đích danh
                    if not standard_time_config:
                        standard_time_config = obj_standard_time_config.search([('department_category', '=', employee_id.department_timesheet_id.category and employee_id.department_timesheet_id.category or ''), ('type', '=', 'no_nominate')], limit=1)
                    #nếu vẫn ko tìm thấy thì báo cmn lỗi đi, đậu xanh bực cả mình.
                    if not standard_time_config:
                        raise except_orm('Thông báo', 'Chưa cấu hình giờ công chuẩn cho chức danh %s ở khối phòng ban %s' % (employee_id.job_id.name, employee_id.department_timesheet_id.category))

                    for key, value in map_day.iteritems():
                        date = month + '-' + str(value)
                        if r[key]:
                            if value <= end_date.day:
                                args = {
                                    'employee_id': r['employee_id'],
                                    'date': date,
                                    'shift_id': r[key],
                                    'standard_time_config_id': standard_time_config and standard_time_config.id or False,
                                    'department_id': employee_id.department_id.id,
                                    'department_timesheet_id': employee_id.department_timesheet_id.id,
                                    'state': 'new',
                                    'priority': priority
                                }

                                new_timesheet = obj_employee_timesheet.create(args)
                                if new_timesheet:
                                    # đoạn này check xem nhân viên có lịch sử nghỉ thai sản or không lương không. nếu có thì không cho xác nhận
                                    check_maternity = obj_hr_maternity_leave_history.search(
                                        [('employee_id', '=', new_timesheet.employee_id.id),
                                         ('date_from', '<=', new_timesheet.date),
                                         ('date_to', '>=', new_timesheet.date)])
                                    if check_maternity and len(check_maternity) >= 1 and new_timesheet.shift_id.name not in ('TS', 'N'):
                                        raise except_orm('Thông báo', 'Không thể phê duyệt được vì có nhân viên [%s] %s phân ca vào ngày đang nghỉ thai sản! Vui lòng liên hệ phòng nhân sự để giải quyết !' % (new_timesheet.employee_id.x_emp_code,new_timesheet.employee_id.name_related, ))
                    employee_timesheets = obj_employee_timesheet.search([('employee_id', '=', r['employee_id']),
                                                                         ('date', '>=', self.period_id.date_start),
                                                                         ('date', '<=', self.period_id.date_stop)])
                    for employee_timesheet in employee_timesheets:
                        TS_obj = self.env['hr.employee.shift'].search([('name', '=', 'TS')])
                        N_obj = self.env['hr.employee.shift'].search([('name', '=', 'N')])
                        check_maternity = obj_hr_maternity_leave_history.search([('employee_id', '=', employee_id.id), ('date_from', '<=',employee_timesheet.date), ('date_to', '>=' , employee_timesheet.date)])
                        if check_maternity and len(check_maternity) >=1:
                            if check_maternity.type == 'maternity_leave':
                                employee_timesheet.write({
                                    'shift_id': TS_obj.id,
                                    'standard_time_config_id': standard_time_config and standard_time_config.id or False,
                                    'department_id': employee_id.department_id.id,
                                    'department_timesheet_id': employee_id.department_timesheet_id.id,
                                    'priority': priority
                                })
                            elif check_maternity.type == 'unpaid_leave':
                                employee_timesheet.write({
                                    'shift_id': N_obj.id,
                                    'standard_time_config_id': standard_time_config and standard_time_config.id or False,
                                    'department_id': employee_id.department_id.id,
                                    'department_timesheet_id': employee_id.department_timesheet_id.id,
                                    'priority': priority
                                })
                        else:
                            employee_timesheet.write({
                                'standard_time_config_id': standard_time_config and standard_time_config.id or False,
                                'department_id': employee_id.department_id.id,
                                'department_timesheet_id': employee_id.department_timesheet_id.id,
                                'priority': priority
                            })
                    priority += 1
                self.write({'state': 'approved'})
            else:
                raise except_orm("Thông báo", "Không có bản ghi nào để phê duyệt")
        else:
            raise except_orm('Thông báo',
                             'Phân ca làm việc có thể đã được trưởng phòng ban thu hồi, refresh trình duyệt để cập nhật lại trạng thái!')

    @api.multi
    def done(self):
        department = self.department_id
        print("department: " + str(department))
        department_ids = self.get_all_child_department(department.id)
        department_ids.append(department.id)
        department_ids = (str(','.join(str(e) for e in department_ids)))
        _logger.error("department_ids: " + str(department_ids))
        query = """SELECT MAX(date) AS max_date FROM hr_employee_timesheet WHERE department_timesheet_id = ANY(string_to_array(%s, ',')::integer[]) AND "state" != 'new' AND date >= %s AND date <= %s"""
        self._cr.execute(query, (department_ids, self.period_id.date_start, self.period_id.date_stop,))
        res = self._cr.dictfetchone()
        if not res['max_date']:
            max_date = datetime.strptime('01/' + self.period_id.code, '%d/%m/%Y').day
        elif res['max_date'] == self.period_id.date_stop:
            raise except_orm('Thông báo', 'Bảng phân ca đã chốt đến ngày cuối cùng!')
        else:
            max_date = (datetime.strptime(res['max_date'], '%Y-%m-%d').day + 1)

        self.from_date = max_date
        view_id = self.env.ref('ev_hr_timesheet.done_hr_shift_assign_form_view').id
        return {
            'name': "Complete timesheet of stage",
            'view_mode': 'form',
            'view_type': 'form',
            'view_id': view_id,
            'res_model': 'hr.shift.assign',
            'res_id': self.id,
            'type': 'ir.actions.act_window',
            'target': 'new',
        }

    @api.multi
    def action_complete(self):
        if self.to_date < self.from_date:
            raise except_orm('Thông báo', 'Đến ngày phải sau từ ngày! Vui lòng chọn lại.')

        obj_employee_timesheet = self.env['hr.employee.timesheet']
        obj_employee_change_shift = self.env['hr.employee.change.shift']
        obj_attendance_exception = self.env['hr.attendance.exception']
        obj_employee_have_child = self.env['hr.employee.have.child']
        obj_employee_going_on_business = self.env['hr.employee.going.on.business']
        obj_employee_overtime = self.env['hr.employee.overtime']
        obj_shift_assign_add = self.env['hr.shift.assign.add']
        obj_shift_assign_detail_add = self.env['hr.shift.assign.detail.add']
        obj_shift_assign_adjust = self.env['hr.shift.assign.adjust']
        obj_shift_assign_detail_adjust = self.env['hr.shift.assign.detail.adjust']
        obj_employee_holiday = self.env['hr.employee.holiday']
        obj_department = self.env['hr.department']

        department_ids = obj_department.get_all_child_department(self.department_id.id)
        department_ids.append(self.department_id.id)
        str_department_ids = (str(','.join(str(e) for e in department_ids)))

        end_date = datetime.strptime(str(self.to_date) + '/' + self.period_id.code, '%d/%m/%Y')
        end_date_str = end_date.strftime('%Y-%m-%d')
        month = end_date.strftime('%Y-%m')
        query = "Select id from hr_employee_timesheet where date::DATE >= %s::DATE and date::DATE <= %s::DATE and department_timesheet_id = ANY(string_to_array(%s, ',')::integer[])"
        self._cr.execute(query, (self.period_id.date_start, end_date_str, str_department_ids))
        res = self._cr.dictfetchall()
        from_date = datetime.strptime(str(self.from_date) + '/' + self.period_id.code, '%d/%m/%Y').strftime('%Y-%m-%d')
        to_date = datetime.strptime(str(self.to_date) + '/' + self.period_id.code, '%d/%m/%Y').strftime('%Y-%m-%d')
        employee_change_shifts = obj_employee_change_shift.search(
            [('department_timesheet_id', 'in', department_ids),
             ('date', '>=', from_date),
             ('date', '<=', to_date),
             ('state', 'not in', ['draft', 'done', 'cancel'])],)
        attendance_exceptions = obj_attendance_exception.search([('department_timesheet_id', 'in', department_ids),
                                                                ('date', '>=', from_date),
                                                                ('date', '<=', to_date),
                                                                ('state', 'not in', ['draft', 'done', 'cancel'])])
        employee_have_childs = obj_employee_have_child.search([('from_date', '>=', from_date),
                                                                 ('from_date', '<=', to_date),
                                                              ('department_timesheet_id', 'in', department_ids),
                                                              ('state', 'not in',
                                                               ['draft', 'approved', 'rejected'])])
        employees_going_on_business = obj_employee_going_on_business.search(
            [('from_date', '>=', from_date),
             ('from_date', '<=', to_date),
             ('department_timesheet_id', 'in', department_ids),
             ('state', 'not in', ['draft', 'approved', 'rejected'])])
        employee_overtimes = obj_employee_overtime.search([('from_date', '>=', from_date),
                                                          ('from_date', '<=', to_date),
                                                          ('department_timesheet_id', 'in', department_ids),
                                                          ('state', 'not in', ['draft', 'done', 'cancel'])])
        shift_assign_detail_adds = obj_shift_assign_detail_add.search([('employee_id.department_timesheet_id', '=', department_ids),
                                            ('init_id.period_id', '=', self.period_id.id),
                                            ('init_id.state', 'not in', ['init', 'draft', 'done', 'cancel'])])
        # shift_assign_add = obj_shift_assign_add.search([('department_id', 'in', department_ids),
        #                                                 ('period_id', '=', self.period_id.id),
        #                                                 ('state', 'not in', ['init', 'draft', 'done', 'cancel'])],
        #                                                limit=1)
        shift_assign_detail_adjusts = obj_shift_assign_detail_adjust.search([('employee_id.department_timesheet_id', '=', department_ids),
                                            ('init_id.period_id', '=', self.period_id.id),
                                            ('init_id.state', 'not in', ['init', 'draft', 'done', 'cancel'])])
        # shift_assign_just = obj_shift_assign_adjust.search([('department_id', 'in', department_ids),
        #                                                 ('period_id', '=', self.period_id.id),
        #                                                 ('state', 'not in', ['init', 'draft', 'done', 'cancel'])],
        #                                                limit=1)
        employee_holidays = obj_employee_holiday.search([('from_date', '>=', from_date),
                                                        ('from_date', '<=', to_date),
                                                        ('department_timesheet_id', 'in', department_ids),
                                                        ('state', 'not in', ['draft', 'done', 'cancel'])])
        str_warning = ''
        if employee_change_shifts:
            str_warning_change_shift = ''
            for employee_change_shift in employee_change_shifts:
                if employee_change_shift.employee_2nd_id:
                    str_warning_change_shift += '[%s]%s | %s - [%s]%s | %s,' % (employee_change_shift.employee_id.x_emp_code, employee_change_shift.employee_id.name_related, employee_change_shift.date,
                                                                                employee_change_shift.employee_2nd_id.x_emp_code, employee_change_shift.employee_2nd_id.name_related, employee_change_shift.date,)
                else:
                    str_warning_change_shift += '[%s]%s | %s,' % (employee_change_shift.employee_id.x_emp_code, employee_change_shift.employee_id.name_related, employee_change_shift.date,)
            str_warning += '(%s) ở chức năng Đổi ca làm việc;\n' % (str_warning_change_shift,)

        if attendance_exceptions:
            str_attendance_exception = ''
            for attendance_exception in attendance_exceptions:
                str_attendance_exception += '[%s]%s | %s,' % (attendance_exception.employee_id.x_emp_code, attendance_exception.employee_id.name_related, attendance_exception.date,)
            str_warning += '(%s) ở chức năng Đến muộn/về sớm;\n' % (str_attendance_exception,)

        if employee_have_childs:
            str_employee_have_child = ''
            for employee_have_child in employee_have_childs:
                str_employee_have_child += '[%s]%s | %s - %s,' % (employee_have_child.employee_id.x_emp_code, employee_have_child.employee_id.name_related, employee_have_child.from_date, employee_have_child.to_date,)
            str_warning += '(%s) ở chức năng Chế độ con nhỏ;\n' % (str_employee_have_child,)

        if employees_going_on_business:
            str_employee_going_on_business = ''
            for employee_going_on_business in employees_going_on_business:
                str_employee_going_on_business += '[%s]%s | %s - %s,' % (employee_going_on_business.employee_id.x_emp_code, employee_going_on_business.employee_id.name_related, employee_going_on_business.from_date, employee_going_on_business.to_date,)
            str_warning += '(%s) ở chức năng Chế độ đi công tác;\n' % (str_employee_going_on_business,)

        if employee_overtimes:
            str_employee_overtime = ''
            for employee_overtime in employee_overtimes:
                str_employee_overtime += '[%s]%s | %s - %s,' % (employee_overtime.employee_id.x_emp_code, employee_overtime.employee_id.name_related, employee_overtime.from_date, employee_overtime.to_date,)
            str_warning += '(%s) ở chức năng Làm việc ngoài giờ;\n' % (str_employee_overtime,)

        if shift_assign_detail_adds:
            str_shift_assign_detail_add = ''
            for shift_assign_detail_add in shift_assign_detail_adds:
                str_shift_assign_detail_add += '[%s]%s | [%s]%s - %s,' % (shift_assign_detail_add.employee_id.x_emp_code, shift_assign_detail_add.employee_id.name_related, shift_assign_detail_add.init_id.department_id.x_department_code, shift_assign_detail_add.init_id.department_id.name, shift_assign_detail_add.init_id.period_id.code,)
            str_warning += '(%s) ở chức năng Bổ sung phân ca;\n' % (str_shift_assign_detail_add,)

        if shift_assign_detail_adjusts:
            str_shift_assign_detail_adjust = ''
            for shift_assign_detail_adjust in shift_assign_detail_adjusts:
                str_shift_assign_detail_adjust += '[%s]%s | [%s]%s - %s,' % (shift_assign_detail_adjust.employee_id.x_emp_code, shift_assign_detail_adjust.employee_id.name_related, shift_assign_detail_adjust.init_id.department_id.x_department_code,shift_assign_detail_adjust.init_id.department_id.name, shift_assign_detail_adjust.init_id.period_id.code,)
            str_warning += '(%s) ở chức năng Điều chỉnh phân ca;\n' % (str_shift_assign_detail_adjust,)
        if employee_holidays:
            str_employee_holiday = ''
            for employee_holiday in employee_holidays:
                str_employee_holiday += '[%s]%s | %s - %s,' % (employee_holiday.employee_id.x_emp_code, employee_holiday.employee_id.name_related, employee_holiday.from_date, employee_holiday.to_date,)
            str_warning += '(%s) ở chức năng Đơn xin nghỉ;\n' % (str_employee_holiday,)
        if len(str_warning) > 0:
            raise except_orm("Thông báo", "Còn các bản ghi " + str_warning + "chưa hoàn thành!")
        if res and len(res) > 0:
            for r in res:
                employee_timesheet = obj_employee_timesheet.search([('id', '=', r['id']), ('state', '=' ,'new')], limit=1)
                employee_timesheet.write({
                    'state': 'closed_shift_assign'
                })
            self.close_timesheet_date = self.to_date
            self.to_date = 1
            if end_date_str >= self.period_id.date_stop:
                self.state = 'done'

        else:
            raise except_orm("Thông báo", "Không có bản ghi nào để hoàn thành")

    @api.multi
    def cancel(self):
        self.state = 'cancel'

    # @api.multi
    # def do_confirm(self):
    #     obj_employee_timesheet = self.env['hr.employee.timesheet']
    #     end_date = datetime.strptime(self.period_id.date_stop, '%Y-%m-%d')
    #     month = end_date.strftime('%Y-%m')
    #     query = "Select * from hr_shift_assign_detail where init_id = %s"
    #     self._cr.execute(query, (self.id,))
    #     res = self._cr.dictfetchall()
    #     if res and len(res) > 0:
    #         for r in res:
    #             for key, value in map_day.iteritems():
    #                 date = month + '-' + str(value)
    #                 if r[key]:
    #                     args = {
    #                         'employee_id': r['employee_id'],
    #                         'date': date,
    #                         'shift_id': r[key],
    #                         'department_id': self.department_id.id
    #                     }
    #                     obj_employee_timesheet.create(args)
    #         self.write({'state': 'done'})
    #     else:
    #         raise except_orm("Thông báo", "Không có bản ghi nào để xác nhận")

    @api.multi
    def do_init_shift(self):
        self.detail_ids.unlink()
        department_obj = self.env['hr.department']
        employee_obj = self.env['hr.employee']
        shift_obj = self.env['hr.employee.shift']
        # obj_employee_holiday_ts = self.env['hr.employee.holiday']

        H_shift = shift_obj.search([('name', '=', 'H')])
        N_shift = shift_obj.search([('name', '=', 'N')])
        TS_shift = shift_obj.search([('name', '=', 'TS')])

        if self.period_id:
            end_date = self.period_id.date_stop
        else:
            raise except_orm('Thông báo', 'Chưa chọn tháng')

        department = self.department_id
        print("department: " + str(department))
        department_ids = self.get_all_child_department(department.id)
        department_ids.append(department.id)
        _logger.error("department_ids: " + str(department_ids))
        for d in department_ids:
            department = department_obj.search([('id', '=', d)])
            query = """
                SELECT a.id FROM hr_employee a
                WHERE a.department_id = %s
                AND a.status in ('working')
                """
            self._cr.execute(query, (department.id, ))
            res = self._cr.dictfetchall()
            if not res and not self.detail_ids: raise except_orm('Thông báo', 'Phòng ban không có nhân viên vào.')

            for r in res:
                employee = employee_obj.search([('id', '=', r['id'])])
                args = {
                    'init_id': self.id,
                    'employee_id': employee.id,
                }
                if employee.default_shift_id:
                    if employee.default_shift_id.name != 'X':
                        for key, value in map_day.items():
                            if value <= end_date.day:
                                args.update({key: employee.default_shift_id.id})
                    else:
                        for key_hc, value_hc in map_day.items():

                            if value_hc <= end_date.day:
                                month = end_date.strftime('%Y-%m')
                                check_day_str = month + '-' + str(value_hc)
                                check_day = datetime.strptime(check_day_str, '%Y-%m-%d')
                                weekday = check_day.weekday()
                                if weekday == 5:  # Saturday
                                    args.update({key_hc: H_shift.id})
                                elif weekday == 6:  # Sunday
                                    args.update({key_hc: N_shift.id})
                                else:
                                    args.update({key_hc: employee.default_shift_id.id})
                else:
                    for key, value in map_day.items():
                        args.update({key: TS_shift.id})
                self.detail_ids.create(args)
        self.state = 'draft'

    @api.multi
    def do_clone_last_month(self):
        print("do_clone_last_month")
        self.detail_ids.unlink()
        obj_hr_department = self.env['hr.department']
        obj_hr_employee = self.env['hr.employee']
        obj_hr_employee_shift = self.env['hr.employee.shift']
        obj_hr_shift_assign = self.env['hr.shift.assign']
        obj_hr_shift_assign_detail = self.env['hr.shift.assign.detail']
        obj_account_period = self.env['account.period']
        obj_employee_holiday_ts = self.env['hr.employee.holiday']
        H_shift = obj_hr_employee_shift.search([('name', '=', 'H')])
        N_shift = obj_hr_employee_shift.search([('name', '=', 'N')])
        TS_shift = obj_hr_employee_shift.search([('name', '=', 'TS')])


        if self.period_id:
            end_date = datetime.strptime(self.period_id.date_stop, '%Y-%m-%d')

            department = self.department_id
            department_ids = self.get_all_child_department(department.id)
            department_ids.append(department.id)
            period_code_last = (datetime.strptime(self.period_id.code, '%m/%Y') - relativedelta(months=1)).strftime(
                '%m/%Y')
            hr_shift_assign = obj_hr_shift_assign.search(
                [('period_id.code', '=', period_code_last and period_code_last or ''),
                 ('department_id', '=', department.id)], limit=1)
            if hr_shift_assign:
                period_id_last = obj_account_period.search([('code', '=', period_code_last)])
                day_start_last = datetime.strptime(period_id_last.date_start, '%Y-%m-%d').weekday()
                day_start_current = datetime.strptime(self.period_id.date_start, '%Y-%m-%d').weekday()
                self._cr.execute(
                    "SELECT employee_id, day_30,day_31,day_18,day_19,day_14,day_15,day_16,day_17,day_10,day_11,day_12,day_13,day_8,day_9,day_2,day_3,"
                    "day_1,day_6,day_7,day_4,day_5,day_21,day_20,day_23,day_22,day_25,day_24,day_27,day_26,day_29,day_28 "
                    "FROM hr_shift_assign_detail WHERE init_id = %s ",
                    (hr_shift_assign and hr_shift_assign.id or 0,))
                hr_shift_assign_details = self._cr.dictfetchall()

                for d in department_ids:
                    department = obj_hr_department.search([('id', '=', d)])
                    employees = obj_hr_employee.search([('department_timesheet_id', '=', department.id), ('status', 'in', ('working', 'maternity_leave'))])
                    if employees and len(employees) > 0:
                        for employee in employees:
                            args = {
                                'init_id': self.id,
                                'employee_id': employee.id,
                            }
                            for key, value in map_day.iteritems():
                                for hr_shift_assign_detail in hr_shift_assign_details:
                                    if hr_shift_assign_detail['employee_id'] == employee.id:
                                        check_ts = False
                                        if int(self.period_id.date_stop[8:10]) >= value:
                                            day_check_holiday = str(self.period_id.date_start[0:7]) + '-' + str(value)
                                            search_hr_employee_holiday_date = obj_employee_holiday_ts.search(
                                                [('state', '=', 'done') ,('employee_id', '=', employee.id), ('from_date', '<=', day_check_holiday), ('to_date', '>=', day_check_holiday)])
                                            if search_hr_employee_holiday_date:
                                                if len(search_hr_employee_holiday_date.employee_holiday_line_ids) >=1:
                                                    for a in search_hr_employee_holiday_date.employee_holiday_line_ids:
                                                        if a.employee_holiday_type_id.category == 'is_maternity':
                                                            check_ts = True
                                        if check_ts is True:
                                            args.update({key: TS_shift.id})
                                        else:
                                            for key_hr_shift_assign_detail, value_hr_shift_assign_detail in hr_shift_assign_detail.iteritems():
                                                if key_hr_shift_assign_detail != 'employee_id' and value <= end_date.day and \
                                                                map_day[key] == map_day[key_hr_shift_assign_detail] + (
                                                                                day_start_last - day_start_current < 0 and day_start_last - day_start_current or day_start_current - day_start_last + 1):
                                                    args.update({key: value_hr_shift_assign_detail})
                            self.detail_ids.create(args)
            else:
                raise except_orm(_("Thông báo"),
                                 _("Tháng trước phòng ban ") + _(department.name) + _(" chưa được phân ca!"))

        else:
            raise except_orm(_('Thông báo'), _('Chưa chọn tháng'))

        self.state = 'draft'

    @api.multi
    def import_file(self):
        print("import_file")
        view_id = self.env.ref('ev_hr_timesheet.import_hr_shift_assign_form_view').id
        return {
            'name': "Change employee shift",
            'view_mode': 'form',
            'view_type': 'form',
            'view_id': view_id,
            'res_model': 'hr.shift.assign',
            'res_id': self.id,
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'new',
        }

    @api.multi
    def read_file(self):
        if not self.file_upload:
            raise except_orm('Error', 'File is not empty')
        department_file = self.check_file_name(self.file_name)
        self.detail_ids.unlink()
        shift_obj = self.env['hr.employee.shift']
        obj_hr_shift_assign_detail = self.env['hr.shift.assign.detail']

        if self.period_id:
            end_date = datetime.strptime(self.period_id.date_stop, '%Y-%m-%d')
            department = self.department_id
            # if department_file != department.id:
            #     raise except_orm('Thông báo', 'Tên file phải là mã phòng ban')
            department_ids = self.get_all_child_department(department.id)
            department_ids.append(department.id)
            data = self.file_upload
            data_file = base64.decodestring(data)
            excel = xlrd.open_workbook(file_contents=data_file)
            sheet = excel.sheet_by_index(0)
            detail_args = []
            employee_assigned_in_month = []
            try:
                if sheet:
                    not_exist_employee = ''
                    for rows in range(sheet.nrows):
                        if rows >= 3:
                            current_row = rows
                            employee_code = _(sheet.cell_value(current_row, 0))
                            if employee_code:
                                employee_code = employee_code.upper()
                                employee_code = employee_code.split('.')[0]
                                query = "Select id from hr_employee where x_emp_code=%s"
                                self._cr.execute(query, (employee_code,))
                                employee_file = self._cr.dictfetchone()
                                if not employee_file:
                                    not_exist_employee += employee_code + ','
                    if len(not_exist_employee) > 0:
                        raise except_orm('Thông báo', _("Không tìm thấy các mã nhân viên: %s") % (not_exist_employee,))
                    for rows in range(sheet.nrows):
                        if rows >= 3:
                            current_row = rows
                            employee_code = sheet.cell_value(current_row, 0)
                            employee_code = str(employee_code).upper()
                            employee_code = employee_code.split('.')[0]
                            query = "Select id, x_emp_code, name_related from hr_employee where x_emp_code=%s"
                            self._cr.execute(query, (employee_code,))
                            employee_file = self._cr.dictfetchone()
                            try:
                                if not employee_file:
                                    raise except_orm('Thông báo! Không Có File')
                            except:
                                raise except_orm('Thông báo',
                                                 _('Không tìm thấy nhân viên có mã: "') + _(employee_code) + _('"') + _(
                                                     '. Dòng ') + _(str(current_row)))
                            if employee_file['id']:
                                shift = False
                                # méo biết bị gì cmt tạm cái đã
                                shift_assign_detail = obj_hr_shift_assign_detail.search(
                                    [('employee_id', '=', employee_file['id']),
                                     ('init_id.period_id', '=', self.period_id.id)], limit=1)
                                if shift_assign_detail: employee_assigned_in_month.append(employee_file['x_emp_code'])
                                hr_shift_assign_detail_temp = {
                                    'employee_id': employee_file['id'],
                                    'init_id': self.id,
                                }
                                for col in range(sheet.ncols):
                                    if col >= 2:
                                        date = sheet.cell_value(2, col)
                                        try:
                                            year, month, day, hour, min, second = xlrd.xldate_as_tuple(date,
                                                                                                       excel.datemode)
                                            date_str = str(year) + "-" + str(month) + "-" + str(day)
                                            # kiểm tra tháng ở file có bằng tháng đã chọn
                                            if month != datetime.strptime(self.period_id.date_start, '%Y-%m-%d').month:
                                                a = 1 / 0
                                        except:
                                            raise except_orm('Thông báo', ("Xem lại ngày ở cột: %s") % ([(col)]))
                                        try:
                                            shift_name = _(sheet.cell_value(current_row, col)).encode("utf-8")
                                            shift_name = str(shift_name).upper().strip()
                                            shift_name = shift_name.split('.')[0]
                                            shift = shift_obj.search([('name', '=', shift_name)])
                                            if not shift and len(shift_name) > 0:
                                                raise except_orm('Thông báo! Không có ca làm việc được cấu hình')
                                        except:
                                            if not shift:
                                                raise except_orm('Thông báo', 'Không tìm thấy ca ' + shift_name)
                                            else:
                                                raise except_orm('Thông báo', _("Xem lại dữ ở cột %s , dòng %s") % (
                                                    col, current_row + 1))
                                        for key, value in map_day.iteritems():
                                            if value <= end_date.day and int(day) == value:
                                                if shift_name == 'TV':
                                                    print("shift_name: TV")
                                                hr_shift_assign_detail_temp.update({
                                                    key: shift and shift.id or False
                                                })
                                detail_args.append((0, 0, hr_shift_assign_detail_temp))
                                if len(employee_assigned_in_month) > 0:
                                    raise except_orm('Thông báo', 'Nhưng nhân viên: ' + str(
                                        employee_assigned_in_month) + ' đã được phân ca trong tháng này!')
                                else:
                                    self.detail_ids = detail_args
            except IndexError:
                raise except_orm("Thông báo", "Danh sách bị Lỗi")
        else:
            raise except_orm('Thông báo', 'Chưa chọn tháng')

        self.state = 'draft'

    @api.multi
    def download_template(self):
        # self.detail_ids.unlink()
        param_obj = self.pool.get('ir.config_parameter')
        base_url = param_obj.get_param(self._cr, self._uid, 'web.base.url')
        url = base_url + '/ev_hr_timesheet/static/template/HMS01.xlsx'
        return {
            "type": "ir.actions.act_url",
            "url": url,
            "target": "_parent",
        }

    def check_file_name(self, file_name):
        if not file_name.endswith('.xls') and not file_name.endswith('.xlsx') and not file_name.endswith('.xlsb'):
            self.file_upload = False
            self.file_name = False
            raise except_orm('Thông báo', "File phải là định dạng 'xlsx' hoặc 'xlsb' hoặc 'xls'")
        department_code = file_name.split('.')[0]
        if department_code:
            department = self.env['hr.department'].search([('x_department_code', '=', department_code)])
            if department and len(department) > 0:
                return department[0].id
            else:
                return False

    def get_all_child_department(self, department_id):
        department_obj = self.env["hr.department"]
        department_ids = []
        departments = department_obj.search([])
        department = department_obj.search([('id', '=', department_id)])
        for d in departments:
            if d.parent_id.id == department.id:
                department_ids.append(d.id)
                temp_arrays = self.get_all_child_department(d.id)
                if len(temp_arrays) > 0:
                    for temp_obj in temp_arrays:
                        department_ids.append(temp_obj)
        return department_ids

    def get_employee_from_user(self):
        query = "select a.id from hr_employee a, resource_resource b where a.resource_id = b.id and b.user_id = %s"
        self._cr.execute(query, (self._uid,))
        res = self._cr.dictfetchone()
        if res:
            return res['id']

    def ir_cron_reminder_sale_all_lead(self, cr, uid):
        # đặt lần chạy tiếp theo
        obj_ir_cron = self.pool['ir.cron']
        to_day = datetime.now()
        last_day_of_month = self.last_day_of_month(to_day + relativedelta(months=1)) - relativedelta(days=2)
        ir_cron = obj_ir_cron.search(cr, uid, [('function', '=', 'ir_cron_reminder_sale_all_lead')], limit=1)
        if ir_cron:
            ir_cron.write({
                'interval_number': 1,
                'nextcall': str(last_day_of_month.year) + '-' + str(last_day_of_month.month) + '-' + str(
                    last_day_of_month.day) + ' 03:00:00',
            })
        print("ir_cron_reminder_sale_all_lead")

        query = """
                    SELECT work_email FROM res_users a
                    LEFT JOIN resource_resource b ON b.user_id = a.id
                    LEFT JOIN hr_employee c ON c.resource_id = b.id
                    LEFT JOIN hr_job d ON d.id = c.job_id
                    WHERE d.code = 'ST'
            """
        cr.execute(query, )
        res = cr.dictfetchall()
        if res:
            for r in res:
                print(r['work_email'])

                # gửi mail
                template = self.pool['ir.model.data'].get_object(cr, 1, 'ev_hr_timesheet',
                                                                 'template_reminder_sale_all_lead1')
                mail_obj = self.pool['mail.timesheet']
                _logger.error("r['work_email']: " + str(r['work_email']))
                mail_id = mail_obj.create(cr, uid, {
                    'email_to': r['work_email'] and r['work_email'] or '',
                    # 'email_to': 'dovietnga0909@gmail.com',
                    'email_cc': 'odoo.izisolution@gmail.com',
                    'subject': _('VMT GROUP'),
                })
                a = self.pool('email.template').send_mail(cr, 1, template.id, mail_id,
                                                          force_send=True)  # , force_send=True

    def ir_cron_reminder_hr_user(self, cr, uid):
        # các shop chưa phân ca
        obj_hr_shift_assign = self.pool['hr.shift.assign']
        obj_account_period = self.pool['account.period']

        shops_not_shift_assign = []
        account_period = obj_account_period.search(cr, uid, [('date_start', '<', datetime.now().strftime('%Y-%m-%d')),
                                                             ('date_stop', '>', datetime.now().strftime('%Y-%m-%d'))])
        print('account_period: ' + str(account_period))
        query_shop = """
                    SELECT a.id, a.x_department_code, a.name FROM hr_department a
                    LEFT JOIN res_partner b ON b.id = a.owner_id
                    WHERE b.is_shop = TRUE
          """
        cr.execute(query_shop, )
        res_shop = cr.dictfetchall()
        if res_shop and account_period:
            for r in res_shop:
                # tý làm tiếp.
                if obj_hr_shift_assign.search(cr, uid, [('department_id', '=', r['id']),
                                                        ('period_id', '=', account_period.id)]) == False:
                    shops_not_shift_assign.append('[' + r['x_department_code' + '] ' + r['name']])

        query = """
                    SELECT work_email FROM res_users a
                    LEFT JOIN resource_resource b ON b.user_id = a.id
                    LEFT JOIN hr_employee c ON c.resource_id = b.id
                    LEFT JOIN hr_job d ON d.id = c.job_id
                    WHERE d.code = 'NS'
            """
        cr.execute(query, )
        res = cr.dictfetchall()
        if res:
            for r in res:
                print(r['work_email'])
                # gửi mail
                template = self.pool['ir.model.data'].get_object(cr, uid, 'ev_hr_timesheet',
                                                                 'template_reminder_hr_user2')
                mail_obj = self.pool['mail.timesheet']
                _logger.error("r['work_email']: " + str(r['work_email']))
                mail_id = mail_obj.create(cr, uid, {
                    'email_to': r['work_email'] and r['work_email'] or '',
                    # 'email_to': 'dovietnga0909@gmail.com',
                    'email_cc': 'odoo.izisolution@gmail.com',
                    'subject': _('VMT GROUP'),
                    'params': {'shops_not_shift_assign': ','.join(shops_not_shift_assign)},
                })
                a = self.pool('email.template').send_mail(cr, 1, template.id, mail_id,
                                                          force_send=True)  # , force_send=True

    def last_day_of_month(self, any_day):
        next_month = any_day.replace(day=28) + relativedelta(days=4)  # this will never fail
        return next_month - relativedelta(days=next_month.day)

    def get_date_from_period(self, cr, uid, period_id):
        if period_id:
            q = '''
                SELECT date_start, date_stop from account_period where id = %s
            '''
            cr.execute(q, (period_id,))
            res = cr.dictfetchone()
            if res:
                return res


class ev_hr_shift_assign_detail(models.Model):
    _name = 'hr.shift.assign.detail'
    # _order = 'employee_id.is_lead_team DESC, employee_id.job_priority asc, employee_id.job_id.id asc, employee_id.name_related asc'

    def _get_total_day_of_month(self):
        for r in self:
            if r.init_id:
                if r.init_id.period_id:
                    end_date = r.init_id.period_id.date_stop
                    r.total_day = end_date.day

    @api.model
    def _domain_shift(self):
        obj_hr_employee = self.env['hr.employee']
        print("self._uid: " + str(self._uid))
        print("self.init_id: " + str(self.init_id))
        hr_employee = obj_hr_employee.search([('user_id', '=', self._uid)], limit=1)
        if hr_employee:
            user_obj = self.env['res.users']
            is_hr_manager = user_obj.has_group('base.group_hr_user')
            if is_hr_manager:
                return []
            else:
                query = """ SELECT hr_employee_shift_id FROM hr_department_hr_employee_shift_rel WHERE hr_department_id = %s"""
                self._cr.execute(query, (hr_employee.department_id.id and hr_employee.department_id.id or 0,))
                res = self._cr.fetchall()
                print("res: " + str(res))
                if res:
                    return [('id', 'in', res)]
                else:
                    return [('id', '=', 0)]

    init_id = fields.Many2one('hr.shift.assign', string='Shift Assign')
    total_day = fields.Integer(string='Total day', compute=_get_total_day_of_month)
    department_id = fields.Many2one('hr.department', compute='_compute_department_id', string='Department', store=True)
    employee_id = fields.Many2one('hr.employee', string='Employee')
    employee_code = fields.Char(string='Employee code', related='employee_id.x_emp_code', readonly=True)
    day_1 = fields.Many2one('hr.employee.shift', domain=_domain_shift, string='1')
    day_2 = fields.Many2one('hr.employee.shift', domain=_domain_shift, string='2')
    day_3 = fields.Many2one('hr.employee.shift', domain=_domain_shift, string='3')
    day_4 = fields.Many2one('hr.employee.shift', domain=_domain_shift, string='4')
    day_5 = fields.Many2one('hr.employee.shift', domain=_domain_shift, string='5')
    day_6 = fields.Many2one('hr.employee.shift', domain=_domain_shift, string='6')
    day_7 = fields.Many2one('hr.employee.shift', domain=_domain_shift, string='7')
    day_8 = fields.Many2one('hr.employee.shift', domain=_domain_shift, string='8')
    day_9 = fields.Many2one('hr.employee.shift', domain=_domain_shift, string='9')
    day_10 = fields.Many2one('hr.employee.shift', domain=_domain_shift, string='10')
    day_11 = fields.Many2one('hr.employee.shift', domain=_domain_shift, string='11')
    day_12 = fields.Many2one('hr.employee.shift', domain=_domain_shift, string='12')
    day_13 = fields.Many2one('hr.employee.shift', domain=_domain_shift, string='13')
    day_14 = fields.Many2one('hr.employee.shift', domain=_domain_shift, string='14')
    day_15 = fields.Many2one('hr.employee.shift', domain=_domain_shift, string='15')
    day_16 = fields.Many2one('hr.employee.shift', domain=_domain_shift, string='16')
    day_17 = fields.Many2one('hr.employee.shift', domain=_domain_shift, string='17')
    day_18 = fields.Many2one('hr.employee.shift', domain=_domain_shift, string='18')
    day_19 = fields.Many2one('hr.employee.shift', domain=_domain_shift, string='19')
    day_20 = fields.Many2one('hr.employee.shift', domain=_domain_shift, string='20')
    day_21 = fields.Many2one('hr.employee.shift', domain=_domain_shift, string='21')
    day_22 = fields.Many2one('hr.employee.shift', domain=_domain_shift, string='22')
    day_23 = fields.Many2one('hr.employee.shift', domain=_domain_shift, string='23')
    day_24 = fields.Many2one('hr.employee.shift', domain=_domain_shift, string='24')
    day_25 = fields.Many2one('hr.employee.shift', domain=_domain_shift, string='25')
    day_26 = fields.Many2one('hr.employee.shift', domain=_domain_shift, string='26')
    day_27 = fields.Many2one('hr.employee.shift', domain=_domain_shift, string='27')
    day_28 = fields.Many2one('hr.employee.shift', domain=_domain_shift, string='28')
    day_29 = fields.Many2one('hr.employee.shift', domain=_domain_shift, string='29')
    day_30 = fields.Many2one('hr.employee.shift', domain=_domain_shift, string='30')
    day_31 = fields.Many2one('hr.employee.shift', domain=_domain_shift, string='31')

    @api.depends('employee_id')
    def _compute_department_id(self):
        for s in self:
            if s.employee_id:
                s.department_id = s.employee_id.department_id

    def set_shift_id(self, cr, uid, update_data):
        for ud in update_data:
            env = api.Environment(cr, uid, {})
            obj_shift_assign_detail = env['hr.shift.assign.detail']
            obj_employee_shift = env['hr.employee.shift']
            shift_assign_detail = obj_shift_assign_detail.search([('id', '=', int(ud['detail_id']))], limit=1)
            if len(ud['shift_name']) == 0:
                employee_shift = False
            else:
                employee_shift = obj_employee_shift.search([('name', '=', ud['shift_name'])], limit=1)
                if not employee_shift:
                    raise except_orm('Thông báo', 'Có lỗi xảy ra, liên hệ Admin để được giải quyết. Không tìm thấy ca.')

            if not shift_assign_detail:
                raise except_orm('Thông báo', 'Có lỗi xảy ra, liên hệ Admin để được giải quyết. Không tìm thấy bản ghi chi tiết.')
            else:
                shift_assign_detail.write({
                    ud['day']: employee_shift and employee_shift.id or False
                })

    def get_shift_assign_detail(self, cr, uid, department_id, period_id):
        print("start: " + str(datetime.now()))
        arr_shift_assign_details = []
        query = """ SELECT a.id, g.id AS department_id, g.name AS department_name, g.x_department_code AS department_code,

                    a.employee_id, c.name_related AS employee_name, c.x_emp_code AS employee_code, d.code AS period_code, d.date_stop
		            , e1.name AS day_01
                    , e2.name AS day_02
                    , e3.name AS day_03
                    , e4.name AS day_04
                    , e5.name AS day_05
                    , e6.name AS day_06
                    , e7.name AS day_07
                    , e8.name AS day_08
                    , e9.name AS day_09
                    , e10.name AS day_10
                    , e11.name AS day_11
                    , e12.name AS day_12
                    , e13.name AS day_13
                    , e14.name AS day_14
                    , e15.name AS day_15
                    , e16.name AS day_16
                    , e17.name AS day_17
                    , e18.name AS day_18
                    , e19.name AS day_19
                    , e20.name AS day_20
                    , e21.name AS day_21
                    , e22.name AS day_22
                    , e23.name AS day_23
                    , e24.name AS day_24
                    , e25.name AS day_25
                    , e26.name AS day_26
                    , e27.name AS day_27
                    , e28.name AS day_28
                    , e29.name AS day_29
                    , e30.name AS day_30
                    , e31.name AS day_31

                    FROM hr_shift_assign_detail a
                     LEFT JOIN hr_shift_assign b ON b.id = a.init_id
                     LEFT JOIN hr_employee c ON c.id = a.employee_id
                     LEFT JOIN account_period d ON d.id = b.period_id
                     LEFT JOIN hr_employee_shift e1 ON e1.id = a.day_1
                     LEFT JOIN hr_employee_shift e2 ON e2.id = a.day_2
                     LEFT JOIN hr_employee_shift e3 ON e3.id = a.day_3
                     LEFT JOIN hr_employee_shift e4 ON e4.id = a.day_4
                     LEFT JOIN hr_employee_shift e5 ON e5.id = a.day_5
                     LEFT JOIN hr_employee_shift e6 ON e6.id = a.day_6
                     LEFT JOIN hr_employee_shift e7 ON e7.id = a.day_7
                     LEFT JOIN hr_employee_shift e8 ON e8.id = a.day_8
                     LEFT JOIN hr_employee_shift e9 ON e9.id = a.day_9
                     LEFT JOIN hr_employee_shift e10 ON e10.id = a.day_10
                     LEFT JOIN hr_employee_shift e11 ON e11.id = a.day_11
                     LEFT JOIN hr_employee_shift e12 ON e12.id = a.day_12
                     LEFT JOIN hr_employee_shift e13 ON e13.id = a.day_13
                     LEFT JOIN hr_employee_shift e14 ON e14.id = a.day_14
                     LEFT JOIN hr_employee_shift e15 ON e15.id = a.day_15
                     LEFT JOIN hr_employee_shift e16 ON e16.id = a.day_16
                     LEFT JOIN hr_employee_shift e17 ON e17.id = a.day_17
                     LEFT JOIN hr_employee_shift e18 ON e18.id = a.day_18
                     LEFT JOIN hr_employee_shift e19 ON e19.id = a.day_19
                     LEFT JOIN hr_employee_shift e20 ON e20.id = a.day_20
                     LEFT JOIN hr_employee_shift e21 ON e21.id = a.day_21
                     LEFT JOIN hr_employee_shift e22 ON e22.id = a.day_22
                     LEFT JOIN hr_employee_shift e23 ON e23.id = a.day_23
                     LEFT JOIN hr_employee_shift e24 ON e24.id = a.day_24
                     LEFT JOIN hr_employee_shift e25 ON e25.id = a.day_25
                     LEFT JOIN hr_employee_shift e26 ON e26.id = a.day_26
                     LEFT JOIN hr_employee_shift e27 ON e27.id = a.day_27
                     LEFT JOIN hr_employee_shift e28 ON e28.id = a.day_28
                     LEFT JOIN hr_employee_shift e29 ON e29.id = a.day_29
                     LEFT JOIN hr_employee_shift e30 ON e30.id = a.day_30
                     LEFT JOIN hr_employee_shift e31 ON e31.id = a.day_31

                     LEFT JOIN hr_job f ON f.id = c.job_id
                     LEFT JOIN hr_department g ON g.id = a.department_id
                    WHERE b.period_id = %s AND b.department_id = %s
                    ORDER BY g.id, c.is_lead_team DESC, c.job_priority, f.priority, c.x_join_date """
        cr.execute(query, (period_id, department_id,))
        res = cr.dictfetchall()
        if res:
            arr_shift_assign_details = []
            for r in res:
                end_day = datetime.strptime(r['date_stop'], '%Y-%m-%d').day
                args = {
                    'id': r['id'],
                    'department_id': r['department_id'],
                    'department_name': r['department_name'],
                    'department_code': r['department_code'],
                    'employee_id': r['employee_id'],
                    'employee_name': r['employee_name'],
                    'employee_code': r['employee_code'],
                    'data': []
                }
                for key, value in sorted(r.iteritems()):
                    if map_day.get(key.replace('_0', '_'), 100) <= end_day:
                        # _logger.error('VINHLDDDDDDDDDDDDDDDDDDDDDDD-------------------------  ' + str(key))
                        # _logger.error('XXXXXXXXXXXXXXXXXXXXXXXXXXXx-------------------------  ' + str(map_day.get(key.replace('_0', '_'), 100)))

                        args['data'].append({
                            'shift_name': value and value or '',
                            'day': key.replace('_0', '_'),
                            'date': datetime.strptime(str(map_day[key.replace('_0', '_')]) + '/' + r['period_code'],
                                                      '%d/%m/%Y').strftime('%Y-%m-%d'),
                        })
                arr_shift_assign_details.append(args)
        return arr_shift_assign_details

    def dialog_error(self, cr, uid, messenger):
        raise except_orm('Thông báo', messenger)
