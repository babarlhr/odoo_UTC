# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import except_orm, ValidationError
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import logging
_logger = logging.getLogger(__name__)



class hr_employee_have_child(models.Model):
    _name = 'hr.employee.have.child'
    _order = 'create_date DESC'

    name = fields.Char(string='Name', default='Have child')
    employee_id = fields.Many2one('hr.employee', string='Employee')
    department_id = fields.Many2one('hr.department', string='Department')
    period_id = fields.Many2one('account.period', string='Month', domain=[('special', '=', False)])
    from_date = fields.Date(string="From date")
    to_date = fields.Date(string="To date")
    type = fields.Selection([('in_late', 'In late'), ('out_early', 'Out early')], default='in_late')
    note = fields.Text(string="Note")
    state = fields.Selection(
        [('draft', 'Draft'), ('wait_approval', 'Wait approval'), ('approved', 'Approved'), ('rejected', 'Rejected'), ('hr_confirm_cancel', 'HR confirm cancel')],
        default='draft')
    # thêm lý do nhân sự từ chối
    reason_cancel = fields.Text(string='Reason cancel')
    # _sql_constraints = [
    #     ('employee_id_period_id_uniq', 'unique(employee_id, period_id)', 'Không thể xin 2 lần trong một tháng!'),
    # ]



    def list_states(self, cr, uid, context=None):
        return [
            ('draft', 'Nháp'),
            ('wait_approval', 'Chờ phê duyệt'),
            ('approved', 'Đã phê duyệt'),
            ('rejected', 'Hủy bỏ'),
        ]


    def list_department(self, cr, uid, context=None):
        query = "SELECT id,x_department_code,name from hr_department order by x_department_code"
        cr.execute(query)
        res = cr.dictfetchall()
        departments = []
        for r in res:
            code = r['x_department_code'] and r['x_department_code'] or ''
            name = r['name'] and r['name'] or ''
            departments.append((r['x_department_code'], code + '_' + name))
        return departments


    def list_region(self, cr, uid, context=None):
        query = "SELECT id,reg_code,name from sc_country_region order by reg_code"
        cr.execute(query)
        res = cr.dictfetchall()
        regions = []
        for r in res:
            code = r['reg_code'] and r['reg_code'] or ''
            name = r['name'] and r['name'] or ''
            regions.append((r['reg_code'], code + '_' + name))
        return regions


    def unlink(self, cr, uid, ids, context=None):
        for line in self.browse(cr, uid, ids):
            if line.state not in ['draft', 'cancel']:
                raise except_orm('Thông báo !', 'Bạn chỉ được phép xóa những bản ghi ở trạng thái nháp !')
            elif line.create_uid.id != uid:
                raise except_orm('Thông báo !', 'Bạn chỉ được phép xóa những bản ghi mà bạn tạo !')
        return super(hr_employee_have_child, self).unlink(cr, uid, ids, context)

    @api.constrains('employee_id')
    def check_employee_id(self):
        #kiểm tra phòng ban
        if self.employee_id:
            if self.employee_id.department_id:
                self.department_id = self.employee_id.department_id.id
            else:
                return {'warning': {
                        'title': _('Thông báo'),
                        'message': _('Chưa cấu hình phòng ban cho nhân viên %s' % (self.employee_id.name_related))
                    }
                }
        #kiểm tra phòng ban chấm công
        if self.employee_id:
            if self.employee_id.department_timesheet_id:
                self.department_timesheet_id = self.employee_id.department_timesheet_id.id
            else:
                return {'warning': {
                        'title': _('Thông báo'),
                        'message': _('Chưa cấu hình phòng ban chấm công cho nhân viên %s' % (self.employee_id.name_related))
                    }
                }

    # @api.onchange('period_id')
    # def onchange_period_id(self):
    #     if self.period_id:
    #         if self.period_id.code < datetime.now().strftime('%m/%Y'):
    #             self.period_id = False
    #             return {'warning': {
    #                     'title': _('Thông báo'),
    #                     'message': _('Không thể chọn tháng đã qua!')
    #                 }
    #             }

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
        now = datetime.now().today()
        date = datetime.strftime(now, '%Y-%m-%d')
        today = datetime.strptime(date, '%Y-%m-%d')
        self_date = datetime.strptime(self.from_date, '%Y-%m-%d')
        user_obj = self.env['res.users']
        is_hr_manager = user_obj.has_group('base.group_hr_user')
        _logger.error(str(is_hr_manager))


        obj_hr_employee_timesheet = self.env['hr.employee.timesheet']

        check_hr_employee_timesheet_is_closed = obj_hr_employee_timesheet.search([('employee_id', '=', self.employee_id.id),
                                                                  ('date', '>=', self.from_date),
                                                                  ('date', '<=', self.to_date),
                                                                  ('state', '<>', 'new')], limit=1)


        #kiểm tra bảng phân ca đã chốt chưa
        if check_hr_employee_timesheet_is_closed:
            raise except_orm('Thông báo', 'Đã chốt phân ca đến những ngày này không thể xin chế độ con nhỏ!')

        #kiểm tra từ ngày nằm trong bản ghi đã xin
        query = '''select id from hr_employee_have_child where employee_id = %s
                    and ((from_date <= %s and to_date >= %s)or (from_date <= %s and to_date >= %s)or (from_date >= %s and to_date <= %s))
                    and state <> 'rejected'
                    and id != %s'''
        self._cr.execute(query, (
            self.employee_id.id, self.from_date, self.from_date, self.to_date, self.to_date, self.from_date,
            self.to_date, self.id))
        res = self._cr.dictfetchall()
        print("res ngadv: " + str(res))
        if res:
            employee_have_child = self.search([('id', '=', res[0]['id'])], limit=1)
            raise except_orm('Thông báo', _('Đã có đơn xin chế độ con nhỏ cho nhân viên  ')
                             + _(employee_have_child.employee_id.name_related)
                             + _(' từ ngày ') + _(employee_have_child.from_date)
                             + _(' đến ngày ') + _(employee_have_child.to_date))

        # kiểm tra phòng ban
        if self.employee_id.department_id:
            self.department_id = self.employee_id.department_id.id
        else:
            raise except_orm('Thông báo', 'Nhân viên không thuộc phòng ban nào!')

        self.state = 'wait_approval'

    @api.multi
    def approval(self):
        self.state = 'approved'

    @api.multi
    def action_cancel(self):
        #kiểm tra trưởng bộ phận:
        self.state = 'hr_confirm_cancel'

    @api.multi
    def action_hr_confirm_cancel(self):
        # kiểm tra trưởng bộ phận:
        view_id = self.env.ref('ev_hr_timesheet.view_hr_employee_have_child_reason_cancel_form').id
        return {
            'name': _('Lý do từ chối'),
            'view_mode': 'form',
            'view_type': 'form',
            'view_id': view_id,
            'res_id': self.id,
            'res_model': 'hr.employee.have.child',
            'type': 'ir.actions.act_window',
            'target': 'new',
        }

    @api.multi
    def confirm_reason_cancel(self):
        self.state = 'rejected'

    @api.multi
    def reject(self):
        view_id = self.env.ref('ev_hr_timesheet.view_hr_employee_have_child_reason_cancel_form').id
        return {
            'name': _('Lý do từ chối'),
            'view_mode': 'form',
            'view_type': 'form',
            'view_id': view_id,
            'res_id': self.id,
            'res_model': 'hr.employee.have.child',
            'type': 'ir.actions.act_window',
            'target': 'new',
        }
    @api.model
    def create(self, vals):
        obj_hr_shift_assign = self.env['hr.shift.assign']
        obj_hr_employee_have_child_manage = self.env['hr.employee.have.child.manage']
        obj_hr_employee_timesheet = self.env['hr.employee.timesheet']

        new = super(hr_employee_have_child, self).create(vals)
        hr_employee_have_child_manage_check = obj_hr_employee_have_child_manage.search([('employee_id', '=', new.employee_id.id)])
        hr_employee_have_child_manage = obj_hr_employee_have_child_manage.search([('employee_id', '=', new.employee_id.id), ('from_date', '<=', new.from_date), ('to_date', '>=', new.to_date), ('active', '=', 't')])
        hr_employee_timesheet = obj_hr_employee_timesheet.search([('employee_id', '=', new.employee_id.id), ('date', '>=', new.from_date), ('date', '<=', new.to_date)], limit=1)

        if hr_employee_timesheet:
            if hr_employee_timesheet.state == 'closed_timesheet':
                raise except_orm('Thông báo', 'Nhân viên này đã chấm công. Vui lòng kiểm tra lại!')

        #
        if len(hr_employee_have_child_manage_check) < 1:
            raise except_orm('Thông báo', 'Chưa cấu hình ngày hưởng chế độ con nhỏ cho nhân viên !')
        if len(hr_employee_have_child_manage) < 1:
            raise except_orm('Thông báo', 'Thời gian xin chế độ con nhỏ không nằm trong khoảng thời gian hưởng chế độ con nhỏ. Vui lòng kiểm tra lại!')

        # kiểm tra phòng ban
        if new.employee_id.department_id:
            new.department_id = new.employee_id.department_id.id
        else:
            raise except_orm('Thông báo', 'Nhân viên không thuộc phòng ban nào!')

        return new

    def daterange(self, from_date, to_date):
        for n in range(int((to_date - from_date).days) + 1):
            yield from_date + timedelta(n)
