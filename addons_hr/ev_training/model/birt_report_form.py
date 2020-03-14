# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from datetime import datetime
from odoo.exceptions import ValidationError


class IziBirtReport(models.TransientModel):
    _name = 'birt.report.timetable'

    session_ids = fields.Many2many('training.session', string='Session')
    from_month = fields.Many2one('account.period', string='From month')
    to_month = fields.Many2one('account.period',string='To month')

    @api.multi
    def create_report_timetable(self):
        report_name = "report_timetable.rptdesign"
        return self.return_report(report_name)

    @api.multi
    def create_report_rating(self):
        report_name = "report_comment_student.rptdesign"
        return self.return_report(report_name)

    @api.multi
    def create_report_rating_major(self):
        report_name = "report_update_skill_consultants.rptdesign"
        return self.return_report(report_name)

    @api.multi
    def create_report_contest(self):
        report_name = "report_update_scores_consultants.rptdesign"
        return self.return_report_date(report_name)

    @api.multi
    def create_report_contest_shop_7(self):
        report_name = "report_update_scores_expert_skincare.rptdesign"
        return self.return_report_date(report_name)

    @api.multi
    def create_report_contest_shop_6(self):
        report_name = "report_update_skill_expert_skincare.rptdesign"
        return self.return_report(report_name)

    @api.multi
    def return_report(self, report_name):
        param_obj = self.env['ir.config_parameter']
        url = param_obj.get_param('report_training')
        if url == False:
            raise ValidationError(_(u"Bạn phải cấu hình birt_url"))
        session_ids = '0'
        if self.session_ids:
            for a in self.session_ids:
                session_ids += ',' + str(a.id)
        return {
            'type': 'ir.actions.act_url',
            'url': url + "report/frameset?__report=report_vmt/" + report_name + "&session=" + str(session_ids),
            'target': 'new',
        }

    @api.multi
    def return_report_date(self, report_name):
        param_obj = self.env['ir.config_parameter']
        url = param_obj.get_param('report_training')
        if url == False:
            raise ValidationError(_(u"Bạn phải cấu hình birt_url"))
        session_ids = '0'
        if self.session_ids:
            for a in self.session_ids:
                session_ids += ',' + str(a.id)
        date = "&from_date=" + str(self.from_month.date_start) + "&to_date=" + str(self.to_month.date_stop)

        return {
            'type': 'ir.actions.act_url',
            'url': url + "report/frameset?__report=report_vmt/" + report_name + "&session=" + str(session_ids) + date,
            'target': 'new',
        }