# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import except_orm


class report_training_contest(models.TransientModel):
    _name = 'training.report.contest'

    date = fields.Date(string='Date')
    major_id = fields.Many2one('training.major', string='Major')
    session_id = fields.Many2one('training.session', string='Session')


    @api.onchange('date')
    def onchange_date(self):
        if self.date:
            if self.session_id.start_date and self.session_id.end_date:
                if self.date[0:10] > self.session_id.end_date[0:10] or self.date[0:10] < self.session_id.start_date[0:10]:
                    raise except_orm('Thông báo', 'Ngày thi phải thuộc ngày hoạt động của lớp')
    @api.multi
    def print_report_contest(self):
        param_obj = self.pool.get('ir.config_parameter')

        url = param_obj.get_param(self._cr, self._uid, 'birt_url')
        report_name = "baocaodanhgiahocvien.rptdesign"
        param_str = "&major_id=" + str(self.major_id.id) + '&date=' + str(self.date) + '&session_id=' + str(self.session_id.id)
        return {
            "type": "ir.actions.act_url",
            "url": url + "" + report_name + param_str,
            "target": "_parent",
        }
