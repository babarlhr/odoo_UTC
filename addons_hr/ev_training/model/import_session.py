# -*- coding: utf-8 -*-
import base64

import xlrd
from odoo import models, fields, api, _
from odoo.exceptions import except_orm
from datetime import datetime, timedelta

class training_employee(models.TransientModel):
    _name = 'training.session.import'

    major_id = fields.Many2one('training.major', string='Major')
    date = fields.Date(string='Date')
    teacher_id = fields.Many2one('training.teacher', string='Teacher')
    xls_file_contest = fields.Binary('File')
    xls_file_timetable = fields.Binary('File')
    file_name = fields.Char(string='File name')
    session_id = fields.Many2one('training.session', string='Session')


    @api.onchange('date')
    def onchange_date(self):
        if self.date:
            if self.session_id:
                if self.date < self.session_id.start_date or self.date > self.session_id.end_date:
                    self.date = False
                    return {'warning': {
                        'title': _('Thông báo'),
                        'message': _('Ngày kiểm tra phải nằm trong thời gian hoạt động của lớp !.')
                    }
                    }

    @api.onchange('major_id')
    def onchange_major(self):
        if self.major_id:
            list_major = []
            for t in self.session_id.timetable_ids:
                list_major.append(t.major_id.id)

            if self.major_id.id not in list_major:
                self.major_id = False
                return {'warning': {
                    'title': _('Thông báo'),
                    'message': _('Môn học này không có trong danh sách thời khóa biểu ! Vui lòng kiểm tra lại.')
                }
                }

    @api.depends('session_id')
    def depend_ses(self):
        self.major_id = self.session_id.timetable_ids.major_id
        self.teacher_id = self.session_id.timetable_ids.teacher_id

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
    def import_xls_timetable(self):
        if not self.xls_file_timetable:
            raise except_orm('Error', 'File is not empty')
        self.check_format_file_excel(self.file_name)
        data = self.xls_file_timetable
        data_file = base64.decodestring(data)
        excel = xlrd.open_workbook(file_contents=data_file)
        sheet = excel.sheet_by_index(0)
        teacher_obj = self.env['training.teacher']
        employee_obj = self.env['hr.employee']
        major_obj = self.env['training.major']
        data = []
        for i in range(1, sheet.nrows):
            end = self.to_string(sheet.cell_value(i, 6))
            start = self.to_string(sheet.cell_value(i, 5))
            startdate = datetime.strptime(start, '%d/%m/%y %H:%M:%S')
            enddate = datetime.strptime(end, '%d/%m/%y %H:%M:%S')
            kc = enddate.hour - startdate.hour
            if kc <= 0:
                raise except_orm('Thông báo', ("Giờ bắt đầu phải lớn hơn giờ kết thúc."))
            if enddate.day != startdate.day:
                raise except_orm('Thông báo', ("Ngày học phải trong cùng một ngày. "))
            elif startdate.date() < self.session_id.start_date or enddate.date() > self.session_id.end_date:
                raise except_orm('Thông báo', ("Thời khóa biểu phải thuộc thời gian của lớp. "))
            # check trùng thời gian
            if data != None:
                for j in range(i-1):
                    if startdate.date() == data[j]['starttime'].date():
                        if startdate.hour == data[j]['starttime'].hour:
                            raise except_orm('Thông báo', ("Trùng thời gian học. "))
                        if startdate.hour > data[j]['endtime'].hour:
                            continue
                        elif startdate.hour == data[j]['endtime'].hour:
                            if startdate.minute >= data[j]['endtime'].minute:
                                continue
                        if enddate.hour < data[j]['starttime'].hour:
                            continue
                        elif enddate.hour == data[j]['starttime'].hour:
                            if enddate.minute <= data[j]['starttime'].minute:
                                pass

                        else:
                            raise except_orm('Thông báo', ("Thời gian học không hợp lệ. "))
                    else:
                        pass
            data.append({
                'starttime': datetime.strptime( self.to_string(sheet.cell_value(i, 5)), '%d/%m/%y %H:%M:%S'),
                'endtime': datetime.strptime( self.to_string(sheet.cell_value(i, 6)), '%d/%m/%y %H:%M:%S')
            })

        try:
            for i in range(1, sheet.nrows):
                major_id = self.to_string(sheet.cell_value(i, 3))
                if major_id:
                    major = major_obj.search([('major_code', '=', major_id.strip())], limit=1)
                    if len(major) < 1:
                        raise except_orm('Thông báo', ("Tên môn không tồn tại: '%s'") % ([
                            (major_id)]))
                else:
                    raise except_orm('Thông báo', ("Thiếu tên môn dòng: '%s'") % ([
                        (i)]))

                end = self.to_string(sheet.cell_value(i, 6))
                start = self.to_string(sheet.cell_value(i, 5))
                startdate = datetime.strptime(start, '%d/%m/%y %H:%M:%S')
                enddate = datetime.strptime(end, '%d/%m/%y %H:%M:%S')
                newstartdate = startdate - timedelta(hours=7)
                newenddate = enddate - timedelta(hours=7)
                kc = enddate.hour - startdate.hour
                if kc <= 0:
                    raise except_orm('Thông báo', ("Giờ bắt đầu phải lớn hơn giờ kết thúc."))

                else:
                    duration = kc
                teacher_id = []
                teacher_name = self.to_string(sheet.cell_value(i, 8))
                if teacher_name:
                    employee_id = employee_obj.search([('x_emp_code', '=', teacher_name.strip())], limit=1)
                    if len(employee_id) < 1:
                        raise except_orm('Thông báo', ("Mã Giáo viên không tồn tại: '%s'") % ([
                            (teacher_name)]))
                    teacher_search = teacher_obj.search([('employee_id', '=', employee_id.id)], limit=1)
                    if len(teacher_search) >= 1:
                        teacher_id = teacher_search

                data = {
                    'session_id': self.session_id and self.session_id.id or False,
                    'major_id': major and major.id or False,
                    'end_time': str(newenddate)[0:17] + '00',
                    'start_time': str(newstartdate)[0:17] + '00',
                    'duration': duration,
                    'employee_ids': '',
                    'state': 'new',
                    'description': None,
                    'teacher_id': teacher_id and teacher_id.id or False,
                }
                upload_file_obj = self.env['training.session.timetable']
                upload_file_obj.create(data)

                self.file_name = None
        except IndexError:
            raise except_orm("Error", "Danh sách bị Thông báo")

    @api.multi
    def import_xls_contest(self):
        major = 0
        for i in range(len(self.session_id.timetable_ids)):
            if self.major_id.id == self.session_id.timetable_ids[i].major_id.id:
                major = 1
        if major != 1:
            raise except_orm('Thông báo', ("Môn '%s' không thuộc lớp học. ") % ([
                (self.major_id).name]))
        employee_obj = self.env['hr.employee']
        if not self.xls_file_contest:
            raise except_orm('Error', 'File is not empty')
        self.check_format_file_excel(self.file_name)
        data = self.xls_file_contest
        data_file = base64.decodestring(data)
        excel = xlrd.open_workbook(file_contents=data_file)
        sheet = excel.sheet_by_index(0)
        data = []
        dem = 0
        for i in range(1, sheet.nrows):
            dem = 0
            for j in range(len(self.session_id.employees_ids)):
                if self.to_string(self.session_id.employees_ids[j].employee_id.x_emp_code) == self.to_string(sheet.cell_value(i, 4)):
                    dem = 1
                    break

            if dem == 0:
                raise except_orm('Thông báo', ("Học viên '%s' không tồn tại trong lớp") % ([
                    (self.to_string(sheet.cell_value(i, 4)))]))

        try:
            line_ids = []
            if self.date > self.session_id.end_date or self.date < self.session_id.start_date:
                raise except_orm('Error', 'Thời gian phải thuộc thời gian mở lớp')
            data = {
                'date': self.date,
                'major_id': self.major_id and self.major_id.id or False,
                'session_id': self.session_id and self.session_id.id or False,
                'teacher_id': self.teacher_id and self.teacher_id.id or False,
                'state': 'new',
                'advantages': '',
                'defect': '',
                'additional_comments': '',
                'ability': '',
            }
            upload_file_obj = self.env['training.session.contest']
            contest = upload_file_obj.create(data)
            for i in range(1, sheet.nrows):
                code_employee = self.to_string(sheet.cell_value(i, 4))
                if code_employee:
                    employee = employee_obj.search([('x_emp_code', '=', code_employee.strip())])
                    if len(employee) < 1:
                        raise except_orm('Thông báo', ("Mã nhân viên không tồn tại: '%s'") % ([
                            (code_employee)]))
                else:
                    raise except_orm('Thông báo', ("Thiếu mã nhân viên dòng: '%s'") % ([
                        (i)]))
                data_line = {
                    'practice_scores': self.to_string(sheet.cell_value(i, 6)),
                    'theory_scores': self.to_string(sheet.cell_value(i, 7)),
                    'employee_id': employee and employee.id or False,
                    'contest_id': contest and contest.id or False,
                    'rating_ids': '',
                    'advantages': self.to_string(sheet.cell_value(i, 9)),
                    'defect': self.to_string(sheet.cell_value(i, 10)),
                    'additional_comments': self.to_string(sheet.cell_value(i, 11)),
                    'ability': self.to_string(sheet.cell_value(i, 12)),
                    'type': self.to_string(sheet.cell_value(i, 13)),
                }
                data = self.env['training.session.contest.line'].create(data_line)
                line_ids.append(data)
            self.file_name = None
        except IndexError:
            raise except_orm("Error", "Danh sách bị Thông báo")

    def check_format_file_excel(self, file_name):
        if file_name.endswith('.xls') is False and file_name.endswith('.xlsx') is False and file_name.endswith(
                '.xlsb') is False:
            self.xls_file = None
            self.file_name = None
            raise except_orm('Thông báo', "File phải là định dạng 'xlsx' hoặc 'xlsb' hoặc 'xls'")