# -*- coding: utf-8 -*-
import logging
from odoo import models, fields, api, _
from datetime import datetime, timedelta
from odoo.exceptions import except_orm, ValidationError
from calendar import monthrange
from dateutil.relativedelta import relativedelta
import random
import math


_logger = logging.getLogger(__name__)
class ev_hr_timesheet(models.Model):
    _name = 'hr.employee.timesheet'

    def _get_duration(self):
        for r in self:
            if r.from_time and r.to_time:
                r.duration = r.to_time - r.from_time

    def _get_shift_time(self):
        for r in self:
            if r.date and r.shift_id:
                shift_from = r.shift_id.from_time - 7
                shift_to = r.shift_id.to_time - 7
                if shift_from < 0 or shift_to < 0:
                    raise except_orm("Thông báo", "Cầu hình ca bị sai")
                if shift_from < 10:
                    str_from_time = '0' + str(timedelta(hours=shift_from))
                else:
                    str_from_time = str(timedelta(hours=shift_from))
                if shift_to < 10:
                    str_to_time = '0' + str(timedelta(hours=shift_to))
                else:
                    str_to_time = str(timedelta(hours=shift_to))
                from_time = r.date + ' ' + str_from_time
                to_time = r.date + ' ' + str_to_time
                r.from_time = from_time
                r.to_time = to_time


    name = fields.Char(string='Name')
    date = fields.Date(string='Date', required=True)
    shift_id = fields.Many2one('hr.employee.shift', string='Shift')
    employee_id = fields.Many2one('hr.employee', string='Employee', required=True)
    employee_code = fields.Char(string='Employee code', related='employee_id.x_emp_code', readonly=True)
    department_id = fields.Many2one('hr.department', string='Department', required=True)
    from_time = fields.Datetime(string='Time from', compute=_get_shift_time)
    to_time = fields.Datetime(string='Time to', compute=_get_shift_time)
    result_id = fields.Many2one('hr.timesheet.result', string='Result')
    priority = fields.Integer(string='Priority')
    note = fields.Text(string='Note')
    holiday_id = fields.Many2one('hr.employee.holiday', string='Holiday')
    standard_time_config_id = fields.Many2one('hr.standard.time.config', string='Standard time config')
    state = fields.Selection(
        [('new', 'New'), ('closed_shift_assign', 'Closed shift assign'), ('closed_timesheet', 'Closed timesheet')])
    overtime = fields.Float(string='Overtime')
    display = fields.Char('Display')

    _sql_constraints = [
        ('employee_date_unique', 'unique(employee_id,date)', 'Nhân viên đã được phân ca trong thời gian này !!!'),
    ]

    @api.constrains('department_id', 'date')
    def check_closing_timesheet(self):
        closing_obj = self.env['hr.closing.timesheet']
        is_open = closing_obj.check_opening(self.department_id.id, self.date)
        if not is_open:
            raise ValidationError("Kỳ chấm công đã đóng, không thể thêm mới")




class employee_timesheet_sheet(models.TransientModel):
    _name = 'employee_timesheet.sheet'

    def _get_default_department(self):
        employee_id = self.get_employee_from_user()
        if employee_id:
            department = self.env['hr.department'].search([('manager_id', '=', employee_id)])
            if department and len(department) > 0:
                return department[0]

    def _get_default_period(self):
        today = datetime.today()
        period = self.env['account.period'].find(today)
        return period

    @api.depends('department_id')
    def _compute_employee_shift(self):
        print("employee_shifts: " )
        # for s in self:
        if self.department_id:
            obj_employee_shift = self.env['hr.employee.shift']
            employee_shifts = obj_employee_shift.search([('department_ids', 'child_of', self.department_id.id)])
            self.employee_shift_ids = employee_shifts

    name = fields.Char(string='Name', default='Timesheet')
    department_id = fields.Many2one('hr.department', string='Department', default=_get_default_department)
    period_id = fields.Many2one('account.period', string='Period', domain=[('special', '=', False)], default=_get_default_period)
    view_type = fields.Selection(
        [('result', 'Result'), ('shift', 'Shift'), ('standard_time', 'Standard time'), ('overtime', 'Overtime'),
         ('total_time', 'Total time')], default='result')
    random = fields.Float()
    employee_shift_ids = fields.One2many('hr.employee.shift', string='Shift', compute=_compute_employee_shift)
    display_type = fields.Selection([('department', 'Department'), ('department_timesheet', 'Department timesheet')], default='department_timesheet', string='Display type')
    from_date = fields.Integer(string='From date')
    to_date = fields.Integer(string='To date')
    close_timesheet_date = fields.Integer(string='Close timesheet date', default=0)

    def get_date_from_period(self, cr, uid, period_id):
        if period_id:
            q = '''
                SELECT date_start, date_stop from account_period where id = %s
            '''
            cr.execute(q, (period_id,))
            res = cr.dictfetchone()
            if res:
                return res

    # @api.multi
    # def action_refresh_sort(self):


    @api.multi
    def action_close_timesheet(self):
        obj_department = self.env['hr.department']

        department_ids = obj_department.get_all_child_department(self.department_id.id)
        department_ids.append(self.department_id.id)
        str_department_ids = (str(','.join(str(e) for e in department_ids)))
        query = """SELECT MAX(date) AS max_date FROM hr_employee_timesheet WHERE department_timesheet_id = ANY(string_to_array(%s, ',')::integer[]) AND "state" = 'closed_timesheet' AND date >= %s AND date <= %s"""
        self._cr.execute(query, (str_department_ids, self.period_id.date_start, self.period_id.date_stop,))
        res = self._cr.dictfetchone()
        if not res['max_date']:
            max_date = datetime.strptime('01/' + self.period_id.code, '%d/%m/%Y').day
        elif res['max_date'] == self.period_id.date_stop:
            raise except_orm('Thông báo', 'Bảng phân ca đã chấm công đến ngày cuối cùng!')
        else:
            max_date = (datetime.strptime(res['max_date'], '%Y-%m-%d').day + 1)

        self.from_date = max_date
        view_id = self.env.ref('ev_hr_timesheet.timesheet_sheet_form_close_timesheet_view').id
        return {
            'name': "Complete timesheet",
            'view_mode': 'form',
            'view_type': 'form',
            'view_id': view_id,
            'res_model': 'employee_timesheet.sheet',
            'res_id': self.id,
            'type': 'ir.actions.act_window',
            'target': 'new',
        }

    #thêm nút mở lại bảng công
    @api.multi
    def open_timesheet(self):
        obj_department = self.env['hr.department']
        department_ids = obj_department.get_all_child_department(self.department_id.id)
        department_ids.append(self.department_id.id)
        str_department_ids = (str(','.join(str(e) for e in department_ids)))
        query = """update  hr_employee_timesheet set "state" = 'closed_shift_assign' WHERE department_timesheet_id = ANY(string_to_array(%s, ',')::integer[]) AND "state" = 'closed_timesheet' AND date >= %s AND date <= %s"""
        self._cr.execute(query, (str_department_ids, self.period_id.date_start, self.period_id.date_stop,))

   #tổng hợp và tính toán lương theo ngày

    @api.multi
    def general_salary(self):
        obj_department = self.env['hr.department']
        obj_statistic_general_timesheet = self.env['hr.statistic.general.timesheet']
        department_ids = obj_department.get_all_child_department(self.department_id.id)
        department_ids.append(self.department_id.id)
        if department_ids:
            for department_id in department_ids:
                department = obj_department.search([('id', '=', department_id)])
                obj_statistic_general_timesheet.action_calculation_salary(department,self.period_id)

    @api.multi
    def action_complete(self):
        if self.to_date < self.from_date:
            raise except_orm('Thông báo', 'Đến ngày phải sau từ ngày! Vui lòng chọn lại.')

        obj_hr_employee_attendance = self.env['hr.employee.attendance']
        obj_hr_statistic_general_timesheet = self.env['hr.statistic.general.timesheet']
        obj_department = self.env['hr.department']
        obj_hr_employee_timesheet = self.env['hr.employee.timesheet']


        from_date = datetime.strptime(str(self.from_date) + '/' + self.period_id.code, '%d/%m/%Y').strftime('%Y-%m-%d')
        to_date = datetime.strptime(str(self.to_date) + '/' + self.period_id.code, '%d/%m/%Y').strftime('%Y-%m-%d')
        # department_ids = obj_department.get_all_child_department(self.department_id.id)
        # department_ids.append(self.department_id.id)
        # str_department_ids = (str(','.join(str(e) for e in department_ids)))

        end_date = datetime.strptime(str(self.to_date) + '/' + self.period_id.code, '%d/%m/%Y')
        end_date_str = end_date.strftime('%Y-%m-%d')

        check_date_close_shift = self.env['hr.employee.timesheet'].search([('department_timesheet_id', '=', self.department_id.id),
                                                                           ('date', '=', end_date_str),('state', '=', 'new')])

        if check_date_close_shift and len(check_date_close_shift) > 0:
            raise except_orm('Thông báo', ("Bảng phân ca chưa chốt đến ngày : %s") % (end_date_str))



        # query = "Select id from hr_employee_timesheet where date::DATE >= %s::DATE and date::DATE <= %s::DATE and department_timesheet_id = ANY(string_to_array(%s, ',')::integer[])"
        # self._cr.execute(query, (self.period_id.date_start, end_date_str, str_department_ids))
        # res = self._cr.dictfetchall()

        hr_employee_attendance = obj_hr_employee_attendance.search([('department_id', '=', self.department_id.id),
                                                                    ('date', '>=', from_date),
                                                                    ('date', '<=', to_date),
                                                                    ('state', '!=', 'done')], limit=1)

        hr_employee_timesheets = obj_hr_employee_timesheet.search(
            [('department_timesheet_id', '=', self.department_id.id), ('date', '>=', self.period_id.date_start),
             ('date', '<=', end_date_str)])

        if hr_employee_attendance:
            raise except_orm('Thông báo',
                             'Hoàn thành hết các bản check-in / check-out trước khi chốt bảng chấm công!')

        for hr_employee_timesheet in hr_employee_timesheets:
            obj_hr_statistic_general_timesheet.job_calculate_statistic_general_timesheet(hr_employee_timesheet.employee_id, self.period_id,
                                                                                         self.department_id, hr_employee_timesheet.date)

            hr_employee_timesheet.write({
                'state': 'closed_timesheet'
            })

        # if res and len(res) > 0:
        #     for r in res:
        #         query = '''update hr_employee_timesheet set state = 'closed_timesheet' WHERE  id = %s '''
        #         self._cr.execute(query, (int(r['id']),))
        # obj_hr_statistic_general_timesheet.job_calculate_statistic_general_timesheet(employees,self.period_id, self.department_id)



    def get_employee_from_user(self):
        query = "select a.id from hr_employee a, resource_resource b where a.resource_id = b.id and b.user_id = %s"
        self._cr.execute(query, (self._uid,))
        res = self._cr.dictfetchone()
        if res:
            return res['id']

    @api.multi
    def do_change_shift(self):
        return {
            'name': "Change employee shift",
            'view_mode': 'form',
            'view_type': 'form',
            'res_model': 'hr.employee.change.shift',
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'new',
        }

    @api.multi
    def print_excel(self):
        param_obj = self.pool.get('ir.config_parameter')
        report_name = "report_timesheet.rptdesign"
        url = param_obj.get_param(self._cr, self._uid, 'birt_url')
        param_str = "&department_id=" + str(self.department_id.id) + \
                    "&from_date=" + self.period_id.date_start + "&to_date=" + self.period_id.date_stop
        return {
            "type": "ir.actions.act_url",
            "url": url + "" + report_name + param_str,
            "target": "_parent",
        }

    @api.multi
    def print_excel_timesheet(self):
        param_obj = self.pool.get('ir.config_parameter')
        report_name = "report_timesheet_result.rptdesign"
        url = param_obj.get_param(self._cr, self._uid, 'birt_url')
        param_str = "&department_id=" + str(self.department_id.id) + \
                    "&from_date=" + self.period_id.date_start + "&to_date=" + self.period_id.date_stop
        return {
            "type": "ir.actions.act_url",
            "url": url + "" + report_name + param_str,
            "target": "_parent",
        }

    @api.multi
    def action_print_report_excel(self):
        param_obj = self.pool.get('ir.config_parameter')
        obj_department = self.env['hr.department']
        url = param_obj.get_param(self._cr, self._uid, 'birt_url')
        department_ids = obj_department.get_all_child_department(self.department_id.id)
        str_department_ids = '0,' + str(self.department_id.id)
        for department_id in department_ids:
            str_department_ids+= ',' + str(department_id)
        param_str = "&department_id=%s&from_date=%s&to_date=%s&department_name=%s"%(str_department_ids, self.period_id.date_start, self.period_id.date_stop, self.department_id.name)
        # param_str = "&department_id=" + str(str_department_ids) + \
        #             "&from_date=" + self.period_id.date_start + "&to_date=" + self.period_id.date_stop

        # print("self.department_id.name: " + _(self.department_id.name))
        # print("self.period_id.name: " + str(self.period_id.name))
        # print("self.view_type: " + str(self.view_type))
        if self.view_type == 'result':#kết quả chấm công
            # SELECT b.x_emp_code, b.name_related, a.date, c.name as rusult_name FROM hr_employee_timesheet a
            # LEFT JOIN hr_employee b ON b.id = a.employee_id
            # LEFT JOIN hr_timesheet_result c ON c.id = a.result_id
            # WHERE a.department_id = 219 AND a."date" >= '2017-07-01' AND a."date" <= '2017-07-31'
            # ORDER BY "date" ASC
            report_name = "report_timesheet_result.rptdesign"
        elif self.view_type == 'standard_time':#giờ công chuẩn
            # SELECT b.x_emp_code, b.name_related, a.date, (c.standard_time * d.standard_time_rate) AS standard_time FROM hr_employee_timesheet a
            # LEFT JOIN hr_employee b ON b.id = a.employee_id
            # LEFT JOIN hr_employee_shift c ON c.id = a.shift_id
            # LEFT JOIN hr_timesheet_result d ON d.id = a.result_id
            # WHERE a.department_id = 219 AND a."date" >= '2017-07-01' AND a."date" <= '2017-07-31'
            # ORDER BY "date" ASC
            report_name = "report_timesheet_standard_time.rptdesign"
        elif self.view_type == 'overtime':#làm thêm giờ
            # SELECT b.x_emp_code, b.name_related, a.date, a.overtime FROM hr_employee_timesheet a
            # LEFT JOIN hr_employee b ON b.id = a.employee_id
            # WHERE a.department_id = 219 AND a."date" >= '2017-07-01' AND a."date" <= '2017-07-31'
            # ORDER BY "date" ASC
            report_name = "report_timesheet_overtime_department.rptdesign"
        elif self.view_type == 'total_time':#tổng thời gian
            # SELECT b.x_emp_code, b.name_related, a.date, ((c.standard_time * d.standard_time_rate) + CASE WHEN a.overtime is null THEN 0
            #         WHEN a.overtime is not null THEN a.overtime
            #    END) AS total_time FROM hr_employee_timesheet a
            # LEFT JOIN hr_employee b ON b.id = a.employee_id
            # LEFT JOIN hr_employee_shift c ON c.id = a.shift_id
            # LEFT JOIN hr_timesheet_result d ON d.id = a.result_id
            # WHERE a.department_id = 219 AND a."date" >= '2017-07-01' AND a."date" <= '2017-07-31'
            # ORDER BY "date" ASC
            report_name = "report_timesheet_total_time.rptdesign"
        else:

            report_name = "report_timesheet.rptdesign"

        return {
            "type": "ir.actions.act_url",
            "url": url + "" + report_name + param_str,
            "target": "_parent",
        }


    @api.multi
    def action_print_report_general(self):
        view_id = self.env.ref('ev_hr_timesheet.hr_report_timesheet_general_form_view').id
        return {
            'name': "Report timesheet",
            'view_mode': 'form',
            'view_type': 'form',
            'view_id': view_id,
            'res_model': 'hr.report.timesheet.general',
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': {'default_department_id': self.department_id.id,
                        }
        }

class ev_hr_timesheet(models.Model):
    _name = 'hr.timesheet.result'

    name = fields.Char(string='Name')
    late_time = fields.Float(string='Late time')
    deduct_amount = fields.Float(string='Deduct amount')
    description = fields.Text(string='Description')
    type = fields.Selection([('on', 'On time'), ('late', 'Late'), ('early', 'Early'), ('holiday', 'Holiday')])
    standard_time_rate = fields.Float(string='Standard time rate')





class hr_report_timesheet_general(models.TransientModel):
    _name = 'hr.report.timesheet.general'

    name = fields.Char(default='New', string='Name')
    from_date = fields.Date(string='From Date')
    to_date = fields.Date(string='To Date')
    department_id = fields.Many2one('hr.department', string='Department')

    @api.onchange('from_date', 'to_date')
    def _onchange_date(self):
        if self.from_date and self.to_date:
            if self.from_date > self.to_date:
                self.to_date = False
                return {'warning': {
                    'title': _('Thông báo'),
                    'message': _('Từ ngày phải nhỏ hơn đến ngày! Vui lòng chọn lại!')
                }
                }
            if str(self.from_date)[0:7] !=  str(self.to_date)[0:7]:
                self.to_date = False
                return {'warning': {
                    'title': _('Thông báo'),
                    'message': _('Không được chọn 2 tháng khác nhau! Vui lòng chọn lại!')
                }
                }

    @api.multi
    def print_report(self):
        obj_department = self.env['hr.department']
        param_obj = self.pool.get('ir.config_parameter')
        # if self.display_type == 'department':
        report_name = "baocaotonghop.rptdesign"
        # elif self.display_type == 'department_timesheet':
        #     report_name = "baocaotonghop_department_timesheet.rptdesign"
        url = param_obj.get_param(self._cr, self._uid, 'birt_url')
        department_ids = obj_department.get_all_child_department(self.department_id.id)
        str_department_ids = '0,' + str(self.department_id.id)
        for department_id in department_ids:
            str_department_ids+= ',' + str(department_id)

        param_str = "&department_id=" + str_department_ids + "&from_date=" + self.from_date + "&to_date=" + self.to_date
        return {
            "type": "ir.actions.act_url",
            "url": url + "" + report_name + param_str,
            "target": "_parent",
        }
