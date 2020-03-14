# -*- coding: utf-8 -*-

from openerp import models, fields, api
from openerp.exceptions import except_orm, ValidationError
from openerp.tools.translate import _
from datetime import datetime
from dateutil.relativedelta import relativedelta
import logging
_logger = logging.getLogger(__name__)




class ev_hr_change_shift(models.Model):
    _name = 'hr.employee.change.shift'
    _order = 'create_date DESC'

    def _get_default_department(self):
        employee_id = self.get_employee_from_user()
        if employee_id:
            department = self.env['hr.department'].search([('manager_id', '=', employee_id)])
            if department and len(department) > 0:
                return department[0]

    @api.model
    def _domain_shift(self):
        obj_hr_employee = self.env['hr.employee']
        print("self._uid: " + str(self._uid))
        hr_employee = obj_hr_employee.search([('user_id', '=', self._uid)], limit=1)
        if hr_employee:
            user_obj = self.env['res.users']
            is_hr_manager = user_obj.has_group('base.group_hr_user')
            if is_hr_manager:
                return []
            else:
                deps_manager = []
                if len(self.get_deps_manager()) > 0:
                    deps_manager = self.get_deps_manager()
                deps_manager.append(hr_employee.department_id.id)
                query = "SELECT hr_employee_shift_id FROM hr_department_hr_employee_shift_rel WHERE hr_department_id in (%s)" % ((str(deps_manager).replace('[', '').replace(']', '')))
                self._cr.execute(query, ())
                res = self._cr.fetchall()
                print("res: " + str(res))
                if res:
                    return [('id', 'in', res)]
                else:
                    return [('id', '=', 0)]

    name = fields.Char(string='Name', default='Change shift')
    department_id = fields.Many2one('hr.department', readonly=True)
    department_timesheet_id = fields.Many2one('hr.department', string="Department timesheet")
    type = fields.Selection([('1_employee', '1 Employee'), ('2_employee', '2 Employee')], default='2_employee',
                            required=True)
    employee_id = fields.Many2one('hr.employee', string='Employee', required=True)
    employee_2nd_id = fields.Many2one('hr.employee', string='Employee 2')
    date = fields.Date(string='Date', required=True)
    old_shift_id = fields.Many2one('hr.employee.shift', domain=_domain_shift,  string='Old shift 1st employee', readonly=True)
    old_shift_2nd_id = fields.Many2one('hr.employee.shift', domain=_domain_shift,  string='Old shift 2nd employee', readonly=True)
    shift_id = fields.Many2one('hr.employee.shift', domain=_domain_shift,  string='New shift 1st employee')
    shift_2nd_id = fields.Many2one('hr.employee.shift', domain=_domain_shift,  string='New shift 2st employee', readonly=True)
    note = fields.Text('Note')
    state = fields.Selection(
        [('draft', 'Draft'), ('confirm', 'Confirm'), ('wait_hr_approval', 'Wait HR approval'), ('done', 'Done'), ('cancel', 'Cancel')],
        default='draft')
    # thêm lý do nhân sự từ chối
    reason_cancel = fields.Text(string='Reason cancel')



    @api.constrains('employee_id', 'employee_2nd_id')
    def check_employee(self):
        if self.type == '2_employee':
            if self.employee_id.department_id.id != self.employee_2nd_id.department_id.id:
                raise ValidationError("Hai nhân viên này không cùng 1 shop")

        #kiểm tra phòng ban
        if self.employee_id:
            if self.employee_id.department_id:
                self.department_id = self.employee_id.department_id.id
            else:
                raise ValidationError('Chưa cấu hình phòng ban cho nhân viên %s' % (self.employee_id.name_related))

    @api.onchange('employee_id', 'date', 'employee_2nd_id')
    def onchange_employee_and_date(self):
        self.department_id = self.employee_id.department_id
        self.old_shift_id = False
        self.shift_id = False
        self.shift_2nd_id = False
        self.old_shift_2nd_id = False

    @api.constrains('department_id', 'date')
    def check_closing_timesheet(self):
        closing_obj = self.env['hr.closing.timesheet']
        print("ngadv 2: " + str(self.employee_id.department_id.id))
        is_open = closing_obj.check_opening(self.employee_id.department_id.id, self.date)
        if not is_open:
            raise ValidationError("Kỳ chấm công đã đóng, không thể thêm mới")

    def unlink(self, cr, uid, ids, context=None):
        for line in self.browse(cr, uid, ids):
            if line.state not in ['draft', 'cancel']:
                raise except_orm('Thông báo !', 'Bạn chỉ được phép xóa những bản ghi ở trạng thái nháp !')
            elif line.create_uid.id != uid:
                raise except_orm('Thông báo !', 'Bạn chỉ được phép xóa những bản ghi mà bạn tạo !')
        return super(ev_hr_change_shift, self).unlink(cr, uid, ids, context)

    @api.multi
    def action_check(self):
        timesheet_obj = self.env['hr.employee.timesheet']
        timesheet = timesheet_obj.search([('employee_id', '=', self.employee_id.id), ('date', '=', self.date)])
        if timesheet and len(timesheet) > 0:
            timesheet = timesheet[0]
            if timesheet.result_id and timesheet.state != 'new':
                raise except_orm('Thông báo', 'Không thể đổi ca khi đã có kết quả chấm công')
            else:
                shift_id = timesheet.shift_id
        else:
            raise except_orm('Thông báo', 'Không tìm thấy bản ghi phân ca của nhân viên 1 trong ngày này')
        if self.type == '2_employee':
            timesheet_2nd = timesheet_obj.search(
                [('employee_id', '=', self.employee_2nd_id.id), ('date', '=', self.date)])
            if timesheet_2nd and len(timesheet_2nd) > 0:
                timesheet_2nd = timesheet_2nd[0]
                shift_id_2nd = timesheet_2nd.shift_id
            else:
                raise except_orm('Thông báo', 'Không tìm thấy bản ghi phân ca của nhân viên 2 trong ngày này')

            if shift_id.id == shift_id_2nd.id:
                raise except_orm('Thông báo', 'Không thể đổi ca 2 nhân viên có ca giống nhau!')

            self.write({
                'old_shift_id': shift_id.id,
                'old_shift_2nd_id': shift_id_2nd.id,
                'shift_id': shift_id_2nd.id,
                'shift_2nd_id': shift_id.id,
            })
        else:
            if self.shift_id.id == timesheet.shift_id.id:
                raise except_orm('Thông báo', 'Không thể đổi 2 ca trùng nhau!')
            self.write({
                'old_shift_id': shift_id.id,
            })
        if 'from_sheet_view' in self._context and self._context['from_sheet_view'] == 1:
            return {
                'name': "Change employee shift",
                'view_mode': 'form',
                'view_type': 'form',
                'res_model': 'hr.employee.change.shift',
                'res_id': self.id,
                'type': 'ir.actions.act_window',
                'nodestroy': True,
                'target': 'new',
            }

    @api.multi
    def do_confirm(self):
        context = self._context
        is_change = False
        is_change_2nd = False
        obj_hr_employee_timesheet = self.env['hr.employee.timesheet']
        timesheet = obj_hr_employee_timesheet.search([('employee_id', '=', self.employee_id.id), ('date', '=', self.date)])

        #Kiểm tra 1 tháng nhân viên chỉ được đổi ca 2 lần

        #nhân viên 1
        query = """
            SELECT "count"(*) FROM hr_employee_change_shift a
              WHERE
                (a.employee_id = %s
                  OR a.employee_2nd_id = %s)
                AND a.state = 'done'
                AND to_char(a.date::date, 'MM-YYYY') = to_char(%s::date, 'MM-YYYY')
                AND a.id <> %s
         """
        self._cr.execute(query, (self.employee_id.id, self.employee_id.id, self.date, self.id))
        res = self._cr.dictfetchone()

        res2 = False
        if self.type == '2_employee':
            #nhân viên 2
            query2 = """
                SELECT "count"(*) FROM hr_employee_change_shift a
                  WHERE
                    (a.employee_id = %s
                      OR a.employee_2nd_id = %s)
                    AND a.state = 'done'
                    AND to_char(a.date::date, 'MM-YYYY') = to_char(%s::date, 'MM-YYYY')
                    AND a.id <> %s
             """
            self._cr.execute(query2, (self.employee_2nd_id.id, self.employee_2nd_id.id, self.date, self.id))
            res2 = self._cr.dictfetchone()

        if res['count'] >= 2 or (res2 and res2['count'] >= 2):
            self.write({
                'state': 'wait_hr_approval'
            })
        else:

            if timesheet and len(timesheet) > 0:
                timesheet = timesheet[0]
                if timesheet.result_id and timesheet.state != 'new':
                    raise except_orm('Thông báo', 'Không thể đổi ca khi đã có kết quả chấm công')
                else:
                    is_change = timesheet.write({'shift_id': self.shift_id.id})
            if self.type == '2_employee':

                timesheet_2nd = obj_hr_employee_timesheet.search(
                    [('employee_id', '=', self.employee_2nd_id.id), ('date', '=', self.date)])
                if timesheet_2nd and len(timesheet_2nd) > 0:
                    timesheet_2nd = timesheet_2nd[0]
                    if timesheet_2nd.result_id and timesheet_2nd.state != 'new':
                        raise except_orm('Thông báo', 'Không thể đổi ca khi đã có kết quả chấm công')
                    else:
                        is_change_2nd = timesheet_2nd.write({'shift_id': self.shift_2nd_id.id})
            if self.type == '1_employee':
                if is_change:
                    self.write({'state': 'done'})
                else:
                    raise except_orm('Thông báo', 'Có lỗi xảy ra, vui lòng thử lại')

            else:
                if is_change and is_change_2nd:
                    self.write({'state': 'done'})
                else:
                    raise except_orm('Thông báo', 'Có lỗi xảy ra, vui lòng thử lại')

            if 'from_sheet_view' in context and context['from_sheet_view'] == 1:
                active_id = context['active_id']
                return {
                    'name': "Change employee shift",
                    'view_mode': 'form',
                    'view_type': 'form',
                    'res_model': 'employee_timesheet.sheet',
                    'res_id': active_id,
                    'type': 'ir.actions.act_window',
                    'nodestroy': True,
                    'target': 'current',
                }

    @api.multi
    def do_confirm_hr_approval(self):
        context = self._context
        is_change = False
        is_change_2nd = False
        obj_hr_employee_timesheet = self.env['hr.employee.timesheet']
        timesheet = obj_hr_employee_timesheet.search([('employee_id', '=', self.employee_id.id), ('date', '=', self.date)])

        if timesheet and len(timesheet) > 0:
            timesheet = timesheet[0]
            if timesheet.result_id and timesheet.state != 'new':
                raise except_orm('Thông báo', 'Không thể đổi ca khi đã có kết quả chấm công')
            else:
                is_change = timesheet.write({'shift_id': self.shift_id.id})
        if self.type == '2_employee':

            timesheet_2nd = obj_hr_employee_timesheet.search(
                [('employee_id', '=', self.employee_2nd_id.id), ('date', '=', self.date)])
            if timesheet_2nd and len(timesheet_2nd) > 0:
                timesheet_2nd = timesheet_2nd[0]
                if timesheet_2nd.result_id and timesheet_2nd.state != 'new':
                    raise except_orm('Thông báo', 'Không thể đổi ca khi đã có kết quả chấm công')
                else:
                    is_change_2nd = timesheet_2nd.write({'shift_id': self.shift_2nd_id.id})
        if self.type == '1_employee':
            if is_change:
                self.write({'state': 'done'})
            else:
                raise except_orm('Thông báo', 'Có lỗi xảy ra, vui lòng thử lại')

        else:
            if is_change and is_change_2nd:
                self.write({'state': 'done'})
            else:
                raise except_orm('Thông báo', 'Có lỗi xảy ra, vui lòng thử lại')

        if 'from_sheet_view' in context and context['from_sheet_view'] == 1:
            active_id = context['active_id']
            return {
                'name': "Change employee shift",
                'view_mode': 'form',
                'view_type': 'form',
                'res_model': 'employee_timesheet.sheet',
                'res_id': active_id,
                'type': 'ir.actions.act_window',
                'nodestroy': True,
                'target': 'current',
            }

    @api.constrains('employee_id', 'employee_2nd_id', 'date', 'state')
    def _check_serial_code(self):
        is_exist = self.search(
            [('employee_id', '=', self.employee_id.id), ('employee_2nd_id', '=', self.employee_2nd_id.id),
             ('date', '=', self.date), ('state', 'not in', ['done', 'cancel']), ('id', '!=', self.id)])
        is_exist_reverse = self.search(
            [('employee_id', '=', self.employee_2nd_id.id), ('employee_2nd_id', '=', self.employee_id.id),
             ('date', '=', self.date), ('state', 'not in', ['done', 'cancel']), ('id', '!=', self.id)])
        if (is_exist and len(is_exist) > 0) or (is_exist_reverse and len(is_exist_reverse) > 0):
            raise ValidationError(_(
                "Đang tồn tại một bản ghi chưa hoàn thành khi thực hiện trong ngày %s giữa 2 nhân viên này") % (
                                      self.date))

    @api.multi
    def do_request(self):
        now = datetime.now().today()
        date = datetime.strftime(now, '%Y-%m-%d')
        today = datetime.strptime(date, '%Y-%m-%d')
        self_date = datetime.strptime(self.date, '%Y-%m-%d')

        obj_hr_employee_timesheet = self.env['hr.employee.timesheet']

        hr_employee_timesheet = obj_hr_employee_timesheet.search([('employee_id', 'in', [self.employee_id.id, self.employee_2nd_id.id, ]),
                                                                  ('date', '=', self.date),
                                                                  ('state', '<>', 'new'),])
        if hr_employee_timesheet:
            raise except_orm('Thông báo', 'Đã chốt phân ca đến ngày này không thể đổi ca là việc!')

        if self.type == '2_employee':
            if self.old_shift_id and self.old_shift_2nd_id and self.shift_id and self.shift_2nd_id:
                self.write({'state': 'confirm'})
            else:
                raise except_orm("Thông báo", "Dữ liệu không hợp lệ")

        else:
            check = False
            for department_id in self.shift_id.department_ids:
                if self.department_id == department_id:
                    check = True
            if not check: raise except_orm('Thông báo', _('Không thể đổi ca mà phòng ban không được sử dụng!'))

            if self.old_shift_id and self.shift_id:
                self.write({'state': 'confirm'})
            else:
                raise except_orm("Thông báo", "Dữ liệu không hợp lệ")

        if 'from_sheet_view' in self._context and self._context['from_sheet_view'] == 1:
            return {
                'name': "Change employee shift",
                'view_mode': 'form',
                'view_type': 'form',
                'res_model': 'hr.employee.change.shift',
                'res_id': self.id,
                'type': 'ir.actions.act_window',
                'nodestroy': True,
                'target': 'new',
            }

    @api.multi
    def do_manager_cancel(self):
        self.write({'state': 'cancel'})

    @api.multi
    def do_hr_cancel(self):
        # kiểm tra trưởng bộ phận:
        view_id = self.env.ref('ev_hr_timesheet.view_hr_employee_change_shift_reason_cancel_form').id
        return {
            'name': _('Lý do từ chối'),
            'view_mode': 'form',
            'view_type': 'form',
            'view_id': view_id,
            'res_id': self.id,
            'res_model': 'hr.employee.change.shift',
            'type': 'ir.actions.act_window',
            'target': 'new',
        }

    @api.multi
    def confirm_reason_cancel(self):
        self.state = 'cancel'

    # def get_employee_from_user(self):
    #     query = "select a.id from hr_employee a, resource_resource b where a.resource_id = b.id and b.user_id = %s"
    #     self._cr.execute(query, (self._uid,))
    #     res = self._cr.dictfetchone()
    #     if res:
    #         return res['id']

    @api.model
    def create(self, vals):
        obj_hr_employee_timesheet = self.env['hr.employee.timesheet']
        new = super(ev_hr_change_shift, self).create(vals)
        hr_employee_timesheet = obj_hr_employee_timesheet.search([('employee_id', 'in', [new.employee_id.id, new.employee_2nd_id.id, ]),
                                                                  ('date', '=', new.date),
                                                                  ('state', '<>', 'new'),])
        if hr_employee_timesheet:
            raise ValidationError('Nhân viên %s đã được chốt phân ca ngày %s, vui lòng chọn lại!' % (hr_employee_timesheet[0].employee_id.name_related, self.date))

        if new.old_shift_id and new.old_shift_2nd_id and new.old_shift_id == new.old_shift_2nd_id:
            raise ValidationError('Không thể đổi 2 ca trùng nhau!')

        return new

    @api.multi
    def write(self, vals):
        res = super(ev_hr_change_shift, self).write(vals)
        obj_hr_employee_timesheet = self.env['hr.employee.timesheet']

        hr_employee_timesheet = obj_hr_employee_timesheet.search([('employee_id', 'in', [self.employee_id.id, self.employee_2nd_id.id, ]),
                                                                  ('date', '=', self.date),
                                                                  ('state', '<>', 'new'),])
        if hr_employee_timesheet:
            raise ValidationError('Nhân viên %s đã được chốt phân ca ngày %s, vui lòng chọn lại!' % (hr_employee_timesheet[0].employee_id.name_related, self.date))

        if self.old_shift_id and self.old_shift_2nd_id and self.old_shift_id == self.old_shift_2nd_id:
            raise ValidationError('Thông báo', 'Không thể đổi 2 ca trùng nhau!')

        return res

    def get_deps_manager(self):
        dep_obj = self.env['hr.department']
        emp_id = self.get_employee_from_user()
        dep = dep_obj.search([('manager_id', '=', emp_id)])
        if dep and len(dep) > 0:
            res = []
            for d in dep:
                res.append(d.id)
            return res
        else:
            return []

    def get_employee_from_user(self):
        user = self.env.user
        cr = self._cr
        if user.id:
            query = "select a.id from hr_employee a, resource_resource b where a.resource_id = b.id and b.user_id = %s LIMIT 1"
            params = (user.id,)
            cr.execute(query, params)
            res = cr.dictfetchone()
        return res and res['id'] or -1

