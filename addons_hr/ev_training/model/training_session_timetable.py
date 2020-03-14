# -*- coding: utf-8 -*-
from datetime import datetime

from odoo import models, fields, api, _
from odoo.exceptions import except_orm


class training_session_timetable(models.Model):
    _name = 'training.session.timetable'

    session_id = fields.Many2one('training.session', string='Session', domain=[('state', '!=', 'done')])
    major_id = fields.Many2one('training.major', string='Major')
    end_time = fields.Datetime(string='End time')
    start_time = fields.Datetime(string='Start time')
    duration = fields.Char(string='Duration')
    employee_ids = fields.One2many('training.session.timetable.line', 'timetable_id', string='Employees')
    state = fields.Selection(selection=(('new', 'New'), ('active', 'Active'), ('done', 'Done'), ('finish', 'Finish')),
                             default='new')
    description = fields.Text(string='Description')
    teacher_id = fields.Many2one('training.teacher', string='Teacher')


    # @api.constrains('start_time', 'end_time')
    # def onchange_start_time_end_time(self):
    #     # if self.session_id:
    #     #     query = '''SELECT end_time, start_time, id from training_session_timetable WHERE  session_id = %s'''
    #     #     self._cr.execute(query, (self.session_id.id,))
    #     #     list = self._cr.dictfetchall()
    #     #     if len(list) > 0:
    #     #         for a in list:
    #     #             if self.start_time and self.end_time:
    #     #                 if self.start_time[0:10] == a['start_time'][0:10]:
    #     #                     if a['start_time'][11:20] < self.start_time[11:20] < a['end_time'][11:20]:
    #     #                         self.end_time = False
    #     #                         self.start_time = False
    #     #                         return {'warning': {
    #     #                             'title': _('Thông báo'),
    #     #                             'message': _('Thời khóa biểu không được trùng nhau!')
    #     #                         }
    #     #                         }
    #     #                         # raise except_orm('Thông báo', 'Thời khóa biểu không được trùng nhau')
    #     #                     if a['start_time'][11:20] < self.end_time[11:20] < a['end_time'][11:20]:
    #     #                         self.end_time = False
    #     #                         self.start_time = False
    #     #                         return {'warning': {
    #     #                             'title': _('Thông báo'),
    #     #                             'message': _('Thời khóa biểu không được trùng nhau!')
    #     #                         }
    #     #                         }
    #     #
    #     #                 if self.end_time[11:17] <= self.start_time[11:17]:
    #     #                     self.end_time = False
    #     #                     self.start_time = False
    #     #                     return {'warning': {
    #     #                         'title': _('Thông báo'),
    #     #                         'message': _('"Từ giờ" phải trước "Đến giờ". Vui lòng chọn lại!')
    #     #                     }
    #     #                     }
    #     #                 if self.start_time[0:10] != self.end_time[0:10]:
    #     #                     self.end_time = False
    #     #                     self.start_time = False
    #     #                     return {'warning': {
    #     #                         'title': _('Thông báo'),
    #     #                         'message': _('Thời gian học phải trong một ngày')
    #     #                     }
    #     #                     }
    #     if self.start_time > self.end_time:
    #         self.end_time = False
    #         return {'warning': {
    #             'title': _('Thông báo'),
    #             'message': _('Giờ kết thúc phải lớn hơn ngày bắt đầu')
    #         }
    #         }
    #
    #     # self.start_time = str(self.start_time)[0:17] + '00'
    #     # self.end_time = str(self.end_time)[0:17] + '00'
    #
    #     if self.start_time and self.session_id.start_date and self.session_id.end_date:
    #         if int(self.start_time[11:13]) > 16:
    #             raise except_orm('Thông báo', 'Thời gian học phải sau 7h ')
    #         if self.session_id.start_date[0:10] > self.start_time[0:10] or self.session_id.end_date[
    #                                                                      0:10] < self.start_time[0:10]:
    #             self.end_time = False
    #             self.start_time = False
    #             return {'warning': {
    #                 'title': _('Thông báo'),
    #                 'message': _('Ngày học phải thuộc ngày lớp học hoạt động')
    #             }
    #             }
    #
    #     if self.start_time and self.end_time:
    #         if int(self.end_time[14:16]) < int(self.start_time[14:16]):
    #             H = int(self.end_time[11:13]) - int(self.start_time[11:13])
    #             m = 60 + int(self.end_time[14:16]) - int(self.start_time[14:16])
    #             self.duration = str(H - 1) + ':' + str(m)
    #
    #         if int(self.end_time[14:16]) >= int(self.start_time[14:16]):
    #             H = int(self.end_time[11:13]) - int(self.start_time[11:13])
    #             m = int(self.end_time[14:16]) - int(self.start_time[14:16])
    #             self.duration = str(H) + ':' + str(m)

    @api.multi
    def action_done(self):
        self.state = 'finish'

    @api.multi
    def action_new(self):
        self.state = 'active'
        if self.state == 'active':
            for a in self.employee_ids:
                a.state = False

    @api.multi
    def action_active(self):
        if self.session_id.state == 'new':
            raise except_orm('Thông báo', 'Lớp chưa hoạt động, vui lòng khởi động lớp')
        self.state = 'active'

    @api.multi
    def reset_to_active(self):
        self.state = 'active'
        if self.state == 'active':
            for a in self.employee_ids:
                a.state = False

    @api.multi
    def active_timetable(self):
        if len(self.teacher_id) < 1:
            raise except_orm('Thông báo', 'Thời khóa biểu chưa có giáo viên')
        if self.session_id.state == 'active':
            self.state = 'active'
        else:
            raise except_orm('Thông báo', 'Lớp chưa hoạt động, vui lòng khởi động lớp')

    @api.multi
    def save_attendance(self):
        self.state = 'done'

    @api.multi
    def report(self):
        param_obj = self.pool.get('ir.config_parameter')
        url = param_obj.get_param(self._cr, self._uid, 'birt_url')
        report_name = "nhat_ky_buoi_hoc.rptdesign"
        param_str = "&timetable_id=" + str(self.id)
        return {
            "type": "ir.actions.act_url",
            "url": url + "" + report_name + param_str,
            "target": "_parent",
        }

    @api.multi
    def attendance_ses(self):
        model, view_id = self.env['ir.model.data'].get_object_reference('ev_training', 'view_training_session_timetable_id_form')
        return {
            'name': 'Timetable',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'training.session.timetable',
            'view_id': view_id,
            'target': 'new',
            'res_id': self.id,
        }

    @api.model
    def create(self, values):
        list = []
        res = super(training_session_timetable, self).create(values)
        for pt_timetable in res.session_id.employees_ids:
            list.append({
                'employee_id': pt_timetable.employee_id.id,
                # 'note': pt_timetable.note,
                'timetable_id': res.id
            })
        res.employee_ids = list
        return res



class training_session_timetable_line(models.Model):
    _name = 'training.session.timetable.line'

    name = fields.Char(string='Name')
    employee_id = fields.Many2one('hr.employee', string='Employee')
    # teacher_id = fields.Many2one('training.teacher', string='Teacher')
    timetable_id = fields.Many2one('training.session.timetable', string='Timetable')
    # Các nút điểm danh:
    # 1. Có mặt
    # 2. Nghỉ có phép
    # 3. Nghỉ không phép
    # 3. Đến muộn quá 10 phút
    state_timetable = fields.Selection(string="State", selection=[('present', 'Có mặt'),
                                                        ('absences_allowed',
                                                         'Nghỉ có phép'),
                                                        ('absences_not_allowed', 'Nghỉ không phép'),
                                                        ('late', 'Đi muộn quá 10 phút'),],
                             required=True, default = 'present')
    note = fields.Text(string='Note')

    # @api.depends('state')
    # def attendance_employee(self):
    #     if self.state == 'present':
    #         self.present += 1
    #     elif self.state == 'absences_allowed':
    #         self.absences_allowed += 1
    #     elif self.state == 'absences_not_allowed':
    #         self.absences_not_allowed += 1
    #     elif self.state == 'late':
    #         self.late += 1
    #     else:
    #         pass
    #
    #     self.sum = self.present + self.absences_allowed + self.absences_not_allowed + self.late


    @api.onchange('employee_id')
    def onchange_employee_id(self):
        if self.employee_id:
            self.name = self.employee_id.name_related
