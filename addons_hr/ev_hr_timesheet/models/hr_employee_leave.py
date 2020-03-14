# -*- coding: utf-8 -*-
from lxml import etree
from odoo import models, fields, api, _
from odoo.exceptions import except_orm, ValidationError
from datetime import datetime
from dateutil.relativedelta import relativedelta


class ev_hr_employee_leave(models.Model):
    _name = 'hr.employee.leave'
    _order = 'from_date desc, department_id'

    name = fields.Char(string='Name', default='/')
    employee_id = fields.Many2one('hr.employee', string='Employee', required=True)
    leave_day = fields.Float(string='Leave day', required=True)
    used_day = fields.Float(string='Used day', required=True)
    remaining_leave_day = fields.Char(string='Remaining leave day', compute='_compute_remaining_leave_day',
                                      readonly=True,)
    from_date = fields.Date(string='From date', required=True)
    rest_leave_day = fields.Float(string='Rest leave day')
    leave_day_last_year = fields.Float(string='Leave day last year')
    remaining_leave_day_last_year = fields.Char(string='Remaining leave day last year', compute='_compute_remaining_leave_day_last_year',
                                      readonly=True,)
    to_date = fields.Date(string='To date', required=True)
    note = fields.Text(string='Note')
    state = fields.Selection([('draft', 'Draft'), ('done', 'Done')], default='draft')
    log_ids = fields.One2many('hr.employee.leave.log', 'leave_id', string='Log')
    key = fields.Text(string='Key')
    department_id = fields.Many2one('hr.department', string="Department")

    @api.depends('leave_day', 'leave_day_last_year')
    def _compute_remaining_leave_day(self):
        for s in self:
            s.remaining_leave_day = s.leave_day - s.used_day

    @api.depends('rest_leave_day', 'leave_day_last_year')
    def _compute_remaining_leave_day_last_year(self):
        for s in self:
            s.remaining_leave_day_last_year = s.rest_leave_day - s.leave_day_last_year

    @api.onchange('employee_id')
    def onchange_employee_id(self):
        #kiểm tra phòng ban
        if self.employee_id:
            if self.employee_id.department_id:
                self.department_id = self.employee_id.department_id.id
            else:
                return {'warning': {
                        'title': _('Thông báo'),
                        'message': _('Nhân viên không thuộc phòng ban nào')
                    }
                }

    @api.constrains('employee_id', 'from_date', 'to_date')
    def valid_employee_leave_day(self):
        if self.to_date < self.from_date:
            raise ValidationError("Ngày kết thúc phải lớn hơn ngày bắt đầu")
        cr = self._cr
        query = '''select id from hr_employee_leave where employee_id = %s
                    and ((from_date < %s and to_date > %s)or (from_date < %s and to_date > %s)or (from_date >%s and to_date < %s))
                    and id != %s'''
        cr.execute(query, (
            self.employee_id.id, self.from_date, self.from_date, self.to_date, self.to_date, self.from_date,
            self.to_date, self.id))
        res = cr.dictfetchall()
        if res and len(res) > 0:
            raise ValidationError("Khoảng thời gian không hợp lệ")

    @api.multi
    def action_confirm(self):
        if self.state == 'draft':
            self.state = 'done'

    def check_leave_day(self, employee_id, date, total_day):
        emp_leave = self.search([('employee_id', '=', employee_id), ('from_date', '<=', date), ('to_date', '>=', date)])
        if emp_leave and len(emp_leave) > 0:
            emp_leave = emp_leave[0]
            date = datetime.strptime(date, '%Y-%m-%d')
            if date + relativedelta(days=total_day - 1) > datetime.strptime(emp_leave.to_date, '%Y-%m-%d'):
                raise except_orm("Thông báo", "Ngày nghỉ phép đã vượt quá kỳ của quỹ nghỉ phép")

            if emp_leave.used_day + total_day <= emp_leave.leave_day:
                return emp_leave
            else:
                raise except_orm("Thông báo", "Số ngày nghỉ phép đã vượt quá số ngày qui định")
        else:
            raise except_orm("Thông báo", "Không tìm thấy quỹ nghỉ phép của nhân viên")

    def update_used_leave_day(self, employee_id, date, total_day):
        emp_leave = self.check_leave_day(employee_id, date, total_day)
        if emp_leave:
            emp_leave.write({'used_day': emp_leave.used_day + total_day})

    # def fields_view_get(self, cr, uid, view_id=None, view_type='form',
    #                     context=None, toolbar=False, submenu=False):
    #     if context is None:
    #         context = {}
    #     res = super(ev_hr_employee_leave,self).fields_view_get(cr, uid, view_id, view_type, context, toolbar, submenu)
    #     mod_obj = self.pool.get('ir.model.data')
    #     obj_res_users = self.pool.get('res.users')
    #     dummy, except_view_id = tuple(mod_obj.get_object_reference(cr, uid, 'ev_hr_timesheet', "hr_shift_assign_form_view"))
    #     print("view_type: " + str(view_type))
    #     if view_type == 'form':
    #         doc = etree.XML(res['arch'])
    #         print(doc)
    #         is_hr_manager = obj_res_users.has_group(cr, uid, 'base.group_hr_user')
    #         if not is_hr_manager:
    #             for node in doc.xpath("//field[@name='name']"):
    #                 node.set('readonly', _("1"))
    #             for node in doc.xpath("//field[@name='employee_id']"):
    #                 node.set('readonly', _("1"))
    #             for node in doc.xpath("//field[@name='leave_day']"):
    #                 node.set('readonly', _("1"))
    #             for node in doc.xpath("//field[@name='used_day']"):
    #                 node.set('readonly', _("1"))
    #             for node in doc.xpath("//field[@name='from_date']"):
    #                 node.set('readonly', _("1"))
    #             for node in doc.xpath("//field[@name='rest_leave_day']"):
    #                 node.set('readonly', _("1"))
    #             for node in doc.xpath("//field[@name='leave_day_last_year']"):
    #                 node.set('readonly', _("1"))
    #             for node in doc.xpath("//field[@name='to_date']"):
    #                 node.set('readonly', _("1"))
    #             for node in doc.xpath("//field[@name='note']"):
    #                 node.set('readonly', _("1"))
    #             for node in doc.xpath("//field[@name='state']"):
    #                 node.set('readonly', _("1"))
    #             for node in doc.xpath("//field[@name='log_ids']"):
    #                 node.set('readonly', _("1"))
    #             for node in doc.xpath("//field[@name='department_id']"):
    #                 node.set('readonly', _("1"))
    #
    #         xarch, xfields = self._view_look_dom_arch(cr, uid, doc, except_view_id, context=context)
    #         res['arch'] = xarch
    #         res['fields'] = xfields
    #     return res


class ev_hr_employee_leave_log(models.Model):
    _name = 'hr.employee.leave.log'

    date = fields.Date(string='Date')
    employee_id = fields.Many2one('hr.employee', string='Employee', required=True)
    add_date = fields.Float('Add date')
    leave_id = fields.Many2one('hr.employee.leave', string= 'Leave')

