# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.tools.translate import _
from odoo.exceptions import except_orm, ValidationError
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import logging
_logger = logging.getLogger(__name__)

class hr_employee_overtime(models.Model):
    _name = 'hr.employee.overtime'
    _order = 'create_date DESC'

    name = fields.Char(string='Name', default='Overtime')
    employee_id = fields.Many2one('hr.employee', string="Employee", required=True)
    department_id = fields.Many2one('hr.department', string="Department")
    overtime = fields.Float(string='Time over', required=True)
    from_date = fields.Date(string='From date', oldname='date', required=True)
    to_date = fields.Date(string='To date', required=True)
    description = fields.Text(oldname='note', string='Description', required=True)
    state = fields.Selection(
        [('draft', 'Draft'), ('confirm', 'Confirm'),
         ('done', 'Done'), ('cancel', 'Cancel')], default='draft')
    type_overtime = fields.Selection([('before_work', 'Before work'), ('after_work', 'After work')], default='', required=True)
    detail_adjust_ids = fields.One2many('hr.employee.overtime.detail.adjust', 'employee_overtime_id', string='Detail adjust overtime')
    is_work_company = fields.Boolean(string='Is work company')
    # thêm lý do nhân sự từ chối
    reason_cancel = fields.Text(string='Reason cancel')
    #

    @api.onchange('overtime')
    def onchage_overtime(self):
        if self.overtime:
            if self.overtime < 1:
                self.overtime = False
                return {'warning': {
                    'title': _('Thông báo'),
                    'message': _('Giờ làm thêm phải lớn hơn 1h')
                }
                }

    @api.multi
    def action_adjust(self):
        self.state = 'confirm'
        context = {
            'default_employee_overtime_id': self.id,
        }
        view = self.env.ref('ev_hr_timesheet.hr_employee_overtime_detail_adjust_form_view')
        return {
            'name': _('Adjust overtime'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'hr.employee.overtime.detail.adjust',
            'views': [(view.id, 'form')],
            'view_id': view.id,
            'target': 'current',
            'context': context,
        }


    def unlink(self, cr, uid, ids, context=None):
        for line in self.browse(cr, uid, ids):
            if line.state not in ['draft', 'cancel']:
                raise except_orm('Thông báo !', 'Bạn chỉ được phép xóa những bản ghi ở trạng thái nháp !')
            elif line.create_uid.id != uid:
                raise except_orm('Thông báo !', 'Bạn chỉ được phép xóa những bản ghi mà bạn tạo !')
        return super(hr_employee_overtime, self).unlink(cr, uid, ids, context)

    @api.constrains('employee_id')
    def check_employee_id(self):
        #kiểm tra phòng ban
        if self.employee_id:
            if self.employee_id.department_id:
                self.department_id = self.employee_id.department_id.id
            else:
                raise ValidationError(_('Chưa cấu hình phòng ban cho nhân viên %s' % (self.employee_id.name_related)))
        #kiểm tra phòng ban chấm công
        if self.employee_id:
            if self.employee_id.department_timesheet_id:
                self.department_timesheet_id = self.employee_id.department_timesheet_id.id
            else:
                raise ValidationError(_('Chưa cấu hình phòng ban chấm công cho nhân viên %s' % (self.employee_id.name_related)))

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

    @api.onchange('overtime')
    def onchange_overtime(self):
        if self.overtime and not (self.overtime*2).is_integer():
            self.overtime = 0.5
            return {'warning': {
                    'title': _('Thông báo'),
                    'message': _('Số giờ làm thêm phải là những giờ như: 0,5 hay 1 hay 1,5 ...! Vui lòng nhập lại')
                }
            }
        #ngày 02/05/2018 chị Thắm bảo có thế bỏ đi. vì ở văn phòng có lúc làm thêm giwof tới 8 tiếng.
        elif self.overtime > 8:
            self.overtime = False
            return {'warning': {
                    'title': _('Thông báo'),
                    'message': _('Không đăng ký quá 8 giờ!')
                }
            }

        # elif self.overtime > 4:
        #     self.overtime = False
        #     return {'warning': {
        #             'title': _('Thông báo'),
        #             'message': _('Không đăng ký quá 4 giờ!')
        #         }
        #     }

    @api.multi
    def send(self):
        now = datetime.now().today()
        date = datetime.strftime(now, '%Y-%m-%d')
        today = datetime.strptime(date, '%Y-%m-%d')
        self_date = datetime.strptime(self.from_date, '%Y-%m-%d')
        obj_hr_employee_timesheet = self.env['hr.employee.timesheet']
        obj_hr_shift_assign = self.env['hr.shift.assign']
        for single_date in self.daterange(datetime.strptime(self.from_date, '%Y-%m-%d'), datetime.strptime(self.to_date, '%Y-%m-%d')):
            hr_employee_timesheet_close = obj_hr_employee_timesheet.search([('employee_id', '=', self.employee_id.id),
                                          ('date', '=', single_date),
                                          ('state', '<>', 'new'),])
            hr_employee_timesheet = obj_hr_employee_timesheet.search([('employee_id', '=', self.employee_id.id), ('date', '=', single_date)], limit=1)

            #kiểm tra từ ngày không nằm trong bản ghi đã xin
            query = '''select id from hr_employee_overtime where employee_id = %s
                        and ((from_date <= %s and to_date >= %s)or (from_date <= %s and to_date >= %s)or (from_date >= %s and to_date <= %s))
                        and state <> 'cancel'
                        and id != %s'''
            self._cr.execute(query, (
                self.employee_id.id, self.from_date, self.from_date, self.to_date, self.to_date, self.from_date,
                self.to_date, self.id))
            res = self._cr.dictfetchall()
            print("res ngadv: " + str(res))
            if res:
                employee_overtime = self.search([('id', '=', res[0]['id'])], limit=1)
                raise except_orm('Thông báo', _('Đã có đơn xin làm việc ngoài giờ cho nhân viên ')
                                 + _(employee_overtime.employee_id.name_related)
                                 + _(' từ ngày ') + _(employee_overtime.from_date)
                                 + _(' đến ngày ') + _(employee_overtime.to_date))
            # employee_overtime = self.env['hr.employee.overtime'].search([('employee_id', '=', self.employee_id.id), ('from_date', '<=', single_date), ('to_date', '>=', single_date), ('id', '!=', self.id), ('state', 'in', ['confirm', 'done'])], limit=1)

            # if employee_overtime:
            #     raise except_orm('Thông báo', 'Ngày ' + str(single_date.strftime('%d-%m-%Y')) + ' đã xin làm thêm giờ, không thể thêm vào ngày này!')
            if hr_employee_timesheet_close:
                raise except_orm('Thông báo', 'Đã chốt phân ca đến ngày '+str(single_date)+' không thể xin làm thêm giờ!')
            if not hr_employee_timesheet:
                raise except_orm('Thông báo', 'Nhân viên chưa được phân ca làm việc trong ngày ' + str(single_date))
            if self.overtime < 1:
                raise except_orm('Thông báo', 'Bạn phải nhập số giờ làm thêm >= 1 !')
            if self.employee_id.department_id:
                self.department_id = self.employee_id.department_id.id
            else:
                raise except_orm('Thông báo', 'Nhân viên không thuộc phòng ban nào!')

        self.write({'state': 'confirm'})

    @api.multi
    def action_make_done(self):
        timesheet_obj = self.env['hr.employee.timesheet']
        timesheets = timesheet_obj.search([('employee_id', '=', self.employee_id.id), ('date', '>=', self.from_date), ('date', '<=', self.to_date)])
        if not timesheets:
            raise except_orm('Thông báo', 'Không tìm thấy bản ghi chấm công của nhân viên trong ngày này')
        # timesheet.write({'overtime': self.overtime})
        self.write({'state': 'done'})

    @api.multi
    def action_cancel(self):

        view_id = self.env.ref('ev_hr_timesheet.view_hr_employee_overtime_reason_cancel_form').id
        return {
            'name': _('Lý do từ chối'),
            'view_mode': 'form',
            'view_type': 'form',
            'view_id': view_id,
            'res_id': self.id,
            'res_model': 'hr.employee.overtime',
            'type': 'ir.actions.act_window',
            'target': 'new',
        }

    @api.multi
    def confirm_reason_cancel(self):
        self.write({'state': 'rejected'})



    @api.model
    def create(self, vals):
        new = super(hr_employee_overtime, self).create(vals)

        #kiểm tra phòng ban
        if new.employee_id.department_id:
            new.department_id = new.employee_id.department_id.id
        else:
            raise except_orm('Thông báo', 'Nhân viên không thuộc phòng ban nào!')

        return new

    def daterange(self, from_date, to_date):
        for n in range(int((to_date - from_date).days) + 1):
            yield from_date + timedelta(n)


class hr_employee_overtime_detail_adjust(models.Model):
    _name = 'hr.employee.overtime.detail.adjust'


    name = fields.Char(default='New')
    employee_overtime_id = fields.Many2one('hr.employee.overtime', string='Overtime')
    date = fields.Date(string="Date", required=True)
    note = fields.Text(string='Note', required=True)
    hours_holiday = fields.Float(string="Hours", required=True)
    type_overtime = fields.Selection([('before_work', 'Before work'), ('after_work', 'After work')], default='', required=True)


    @api.onchange('hours_holiday')
    def onchage_hours_holiday(self):
        if self.hours_holiday:
            if self.hours_holiday < 1:
                self.hours_holiday = False
                return {'warning': {
                    'title': _('Thông báo'),
                    'message': _('Giờ làm thêm phải lớn hơn 1h')
                }
                }


    @api.onchange('date', 'type_overtime')
    def onchange_date_overtime(self):
        if self.employee_overtime_id:
            if self.date:
                if self.date < self.employee_overtime_id.from_date or self.date > self.employee_overtime_id.to_date:
                    self.date = False
                    return {'warning': {
                        'title': _('Thông báo'),
                        'message': _('"Ngày điều chỉnh phải thuộc từ ngày đến ngày của đăng ký làm thêm giờ!')
                    }
                    }

                if self.type_overtime:
                    # count =0
                    for x in self.employee_overtime_id.detail_adjust_ids:
                        if x.date == self.date and self.type_overtime == x.type_overtime and x.id != self.id:
                            self.date = False
                            self.type_overtime = False
                            return {'warning': {
                                'title': _('Thông báo'),
                                'message': _('"Có 1 bản ghi điều chỉnh tương tự. Vui lòng kiểm tra lại !!!')
                            }
                            }

