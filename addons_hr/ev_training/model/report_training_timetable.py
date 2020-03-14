# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import except_orm

class report_training_timetable(models.TransientModel):
    _name = 'training.report.timetable'

    session_id = fields.Many2one('training.session', string='Session')
    major_id = fields.Many2one('training.major', string='Major')
    end_time = fields.Datetime(string='End time')
    start_time = fields.Datetime(string='Start time')
    duration = fields.Char(string='Duration')


    @api.onchange('start_time')
    def onchange_start_time(self):
        if self.start_time:
            self.end_time = self.start_time
            if self.session_id.start_date and self.session_id.end_date:
                if self.start_time[0:10] > self.session_id.end_date[0:10] or self.end_time[0:10] < self.session_id.start_date[0:10]:
                    raise except_orm('Thông báo', 'Ngày điểm danh phải thuộc ngày lớp hoạt động')

    @api.onchange('end_time')
    def onchange_end_time(self):
        if self.end_time and self.start_time:
            if self.end_time[0:10] != self.start_time[0:10]:
                raise except_orm('Thông báo', 'Giờ kết thúc và giờ bắt đầu phải cùng một ngày')

    @api.onchange('start_time', 'end_time')
    def onchange_start_time_end_time(self):
        if self.start_time and self.end_time:
            H = int(self.end_time[11:13]) - int(self.start_time[11:13])
            m = int(self.end_time[14:16]) - int(self.start_time[14:16])

            if m >= 0:
                self.duration = str(H) + ':' + str(m)
            else:
                self.duration = str(H - 1) + ':' + str(abs(m))

    @api.multi
    def print_report_timetable(self):
        param_obj = self.pool.get('ir.config_parameter')

        url = param_obj.get_param(self._cr, self._uid, 'birt_url')
        report_name = "baocaodiemdanh.rptdesign"
        param_str = "&session_id=" + str(self.session_id.id) + "&major_id=" + str(self.major_id.id) + "&start_time=" + str(self.start_time) + "&end_time=" + str(self.end_time)
        return {
            "type": "ir.actions.act_url",
            "url": url + "" + report_name + param_str,
            "target": "_parent",
        }
