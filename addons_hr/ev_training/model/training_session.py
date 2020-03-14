# -*- coding: utf-8 -*-
import base64
import logging

import xlrd

from odoo import models, fields, api, _
from odoo.exceptions import except_orm

_logger = logging.getLogger(__name__)


class training_employee(models.Model):
    _name = 'training.session.employee'

    name = fields.Char(string='Name')
    employee_id = fields.Many2one('hr.employee', string='Employee')
    session_id = fields.Many2one('training.session', string='Session')
    course_id = fields.Many2one(related='session_id.course_id', string='Course')
    date_from_course = fields.Date(related='course_id.start_date', string='From date')
    date_to_course = fields.Date(related='course_id.end_date', string='To date')
    note = fields.Text(string='Note')

    def name_get(self, cr, uid, ids, context=None):
        employees = self.browse(cr, uid, ids)
        # lấy ra toàn bộ bản ghi
        results = []
        for line in employees:
            # lấy ra từng bản ghi của timetable_lines đặt vào mảng
            results.append((line.id, line.employee_id.name))

        return results

    @api.onchange('employee_id')
    def onchange_employee_id(self):
        if self.employee_id:
            self.name = self.employee_id.name


class training_session(models.Model):
    _name = 'training.session'
    _order = 'id desc'

    name = fields.Char(string='Name')
    code = fields.Char(string=('Code'), help=('The code will be generated automatically'), default='',
                       compute='change_code')
    course_id = fields.Many2one('training.course', string='Course', domain=[('state', '!=', 'done')])
    description = fields.Text(string='Description')
    start_date = fields.Date(string='Start date')
    end_date = fields.Date(string='End date')
    timetable_ids = fields.One2many('training.session.timetable', 'session_id', string='Timetable')
    teacher_ids = fields.One2many('training.session.teacher', 'session_id', string='Manager')
    employees_ids = fields.One2many('training.session.employee', 'session_id', string='Employees')
    state = fields.Selection(selection=(('new', 'New'), ('active', 'Active'), ('done', 'Done')),
                             default='new')
    contest_ids = fields.One2many('training.session.contest', 'session_id', string='Contest')
    xls_file = fields.Binary('File')
    file_name = fields.Char(string='File name')
    header_code = fields.Char(string='Header code', help=('The code will be generated automatically'),
                               default='',)
    footer_code = fields.Integer(string='Footer code', digits=(6, 0),)

    def generate_code(self):
        if self.footer_code > 9 and self.footer_code < 100:
            data ='00'
        elif self.footer_code <= 9:
            data = '000'
        else:
            data = '0'
        return data


    @api.onchange('header_code')
    def change_footer_code(self):
        if self.header_code:
            self.header_code = str(self.header_code).upper()
            query = '''SELECT footer_code, header_code FROM training_session WHERE header_code = %s'''
            self._cr.execute(query, (str(self.header_code).upper(),))
            res = self._cr.dictfetchall()
            data = []
            for i in res:
                data.append(i['footer_code'])

            if res:
                self.footer_code = max(data) + 1
            else:
                self.footer_code = 1
        else:
            pass

    @api.depends('footer_code', 'header_code')
    @api.one
    def change_code(self):
        self.code = str(self.header_code) + '/' + str(self.generate_code()) + str(self.footer_code)

    @api.multi
    def contest_import(self):
        model, view_id = self.env['ir.model.data'].get_object_reference('ev_training', 'view_act_import_contest')
        return {
            'name': 'Contest',
            'type': 'ir.actions.act_window',
            'res_model': 'training.session.import',
            'view_mode': 'form',
            'view_id': view_id,
            'target': 'new',
            'context': {'default_session_id': self.id, },
        }

    @api.multi
    def timetable_import(self):
        model, view_id = self.env['ir.model.data'].get_object_reference('ev_training', 'view_act_import_timetable')
        return {
            'name': 'Timetable',
            'type': 'ir.actions.act_window',
            'res_model': 'training.session.import',
            'view_mode': 'form',
            'view_id': view_id,
            'target': 'new',
            'context': {'default_session_id': self.id},
        }


    def is_number(self, s):
        try:
            float(s)
            return True
        except ValueError:
            return False

    def to_string(self, s):
        if self.is_number(s):
            result = str(int(s))
            return result
        else:
            return s

    @api.multi
    def import_xls_employee(self):
        lines = []
        employee_obj = self.env['hr.employee']
        if not self.xls_file:
            raise except_orm('Error', 'File is not empty')
        self.check_format_file_excel(self.file_name)
        data = self.xls_file
        data_file = base64.decodestring(data)
        excel = xlrd.open_workbook(file_contents=data_file)
        sheet = excel.sheet_by_index(0)
        try:
            for i in range(1, sheet.nrows):

                code_employee = self.to_string(sheet.cell_value(i, 1))
                if code_employee:
                    employee = employee_obj.search([('x_emp_code', '=', str(code_employee.strip()))])
                    if employee:
                        for j in range(0, i):
                            if self.to_string(sheet.cell_value(j, 1)) == self.to_string(sheet.cell_value(i, 1)):
                                raise except_orm('Thông báo', ("Mã nhân viên : '%s' đã tồn tại") % ([
                                    (code_employee)]))

                    if len(employee) < 1:
                        raise except_orm('Thông báo', ("Mã nhân viên không tồn tại: '%s'") % ([
                            (code_employee)]))

                    for item in self.employees_ids:
                        if str(code_employee.strip()) == item.employee_id.x_emp_code:
                            raise except_orm('Thông báo', ("Mã nhân viên không được trùng nhau : '%s'") % ([
                                (item.employee_id.x_emp_code)]))

                else:
                    raise except_orm('Thông báo', ("Thiếu mã nhân viên dòng: '%s'") % ([
                        (i)]))

                data = {
                    'name': employee.name or False,
                    'employee_id': employee and employee.id or False,
                    'session_id': self and self.id or False,
                    'course_id': self.course_id or False,
                    'date_from_course': self.course_id.start_date or False,
                    'date_to_course': self.course_id.end_date or False,
                    'note': self.to_string(sheet.cell_value(i, 3)) or False,

                }

                upload_file_obj = self.env['training.session.employee']
                upload_file_obj.create(data)

        except IndexError:
            raise except_orm("Error", "Danh sách bị Thông báo")

    def check_format_file_excel(self, file_name):
        if file_name.endswith('.xls') is False and file_name.endswith('.xlsx') is False and file_name.endswith(
                '.xlsb') is False:
            self.xls_file = None
            self.file_name = None
            raise except_orm('Thông báo', "File phải là định dạng 'xlsx' hoặc 'xlsb' hoặc 'xls'")

    @api.onchange('course_id')
    def onchange_course_id(self):
        if self.course_id:
            if self.course_id.state == 'done':
                raise except_orm('Thông báo', 'Khóa học này đã kết thúc! Vui lòng chọn lại')

    # @api.onchange('timetable_ids')
    # def onchange_timetable_ids(self):
    #     for index in range(len(self.timetable_ids)):
    #         for index1 in range(len(self.timetable_ids)):
    #             if index != index1:
    #                 if self.timetable_ids[index].start_time[:10] == self.timetable_ids[index1].start_time[:10]:
    #                     if self.timetable_ids[index].start_time[11:20] < self.timetable_ids[index1].start_time[11:20] < \
    #                             self.timetable_ids[index].end_time[11:20] or self.timetable_ids[index].start_time[
    #                                                                          11:20] < self.timetable_ids[
    #                                                                                       index1].end_time[11:20] < \
    #                             self.timetable_ids[index].end_time[11:20]:
    #                         raise except_orm('Thông báo', 'Thời khóa biểu không được trùng nhau')
    @api.multi
    def write(self, vals):
        res = super(training_session, self).write(vals) # bản ghi mới được chỉnh
        for index in range(len(self.employees_ids)):
            for index1 in range(len(self.employees_ids)):
                if index != index1:
                    if str(self.employees_ids[index].employee_id.x_emp_code) == str(self.employees_ids[index1].employee_id.x_emp_code):
                        raise except_orm('Thông báo', 'Học viên không được trùng nhau')
        return res

    @api.onchange('teacher_ids')
    def onchange_teacher_ids(self):
        for a in range(len(self.teacher_ids)):
            for b in range(len(self.teacher_ids)):
                if a != b:
                    if self.teacher_ids[a].major_id.id == self.teacher_ids[b].major_id.id:
                        raise except_orm('Thông báo', 'Môn học của lớp không được trùng nhau')

    @api.onchange('employees_ids')
    def onchange_employees_ids(self):
        # a = self.employees_ids
        # b = self.employees_ids
        for index1 in range(len(self.employees_ids)):
            # print  index1
            for index2 in range(len(self.employees_ids)):
                if index1 != index2:
                    if self.employees_ids[index1].employee_id.id == self.employees_ids[index2].employee_id.id:
                        raise except_orm('Thông báo', 'Học viên không được trùng nhau')

    @api.onchange('start_date', 'end_date')
    def onchange_start_date_end_date(self):
        if self.start_date and self.end_date and self.course_id.start_date and self.course_id.end_date:
            if self.start_date[0:10] < self.course_id.start_date[0:10] or self.end_date[
                                                                          0:10] > self.course_id.end_date[0:10]:
                raise except_orm('Thông báo', 'Ngày bắt đầu và kết thúc của lớp học phải phụ thuộc khóa hoc')

    @api.onchange('end_date')
    def onchange_end_date(self):
        if self.end_date and self.start_date:
            if self.end_date < self.start_date:
                self.end_date = False
                self.start_date = False
                return {'warning': {
                    'title': _('Thông báo'),
                    'message': _('"Ngày bắt đầu" không lớn hơn "Ngày kết thúc". Vui lòng chọn lại!')
                }
                }

    @api.multi
    def action_active(self):
        if self.name != False :
            if len(self.employees_ids) == 0:
                raise except_orm('Thông báo', 'Lớp học phải có học viên và giáo viên mới được khởi động')

        self.state = 'active'

    @api.multi
    def contest(self):
        model, view_id = self.env['ir.model.data'].get_object_reference('ev_training', 'view_training_session_contest_contest_form')
        return {
            'name': 'Contest',
            'type': 'ir.actions.act_window',
            'res_model': 'training.session.contest',
            'view_mode': 'form',
            'view_id': view_id,
            'target': 'current',
        }

    @api.multi
    def reset_to_active(self):
        self.timetable_ids.state = 'active'

    @api.multi
    def action_done(self):
        if self.employees_ids:
            for st in self.employees_ids:
                st.state = 'done'
        if self.timetable_ids:
            for s in self.timetable_ids:
                if s.state != 'done':
                    raise except_orm(('Phát hiện sai'),
                                     ('Không được phép kết thúc lớp  khi các lớp chưa điểm danh'))
        self.state = 'done'
        if self.state == 'done':
            for a in self.timetable_ids:
                a.state = 'finish'


class training_teacher(models.Model):
    _name = 'training.session.teacher'

    name = fields.Char(string='Name')
    teacher_id = fields.Many2one('training.teacher', string='Teacher')
    session_id = fields.Many2one('training.session', string='Session')
    major_id = fields.Many2one('training.major', string='Major')  # chuyên ngành


class ev_hr_employee_session(models.Model):
    _inherit = 'hr.employee'

    session_ids = fields.One2many('training.session.employee', 'employee_id', string='Sessions')
    level_id = fields.Many2one('level.employee.config', string='Level')
