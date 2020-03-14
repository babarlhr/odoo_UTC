# -*- coding: utf-8 -*-

from openerp import models, fields, api, _
from datetime import datetime
from openerp.exceptions import ValidationError

class Izi_report_recruitment(models.TransientModel):
    _name = 'birt.report.recruitment'

    recruitment_session_id = fields.Many2many('hr.recruitment.session', string='Recruitment')

    job_applicant_id = fields.Many2one('hr.job', string='Job',)

    @api.multi
    def create_report_recruitment_session_applicant(self):
        report_name = "report_recruiment_applicant.rptdesign"
        return self.return_report_recruitment_applicant(report_name)

    @api.multi
    def create_report_recruitment_session(self):
        report_name = "report_recruitment_session.rptdesign"
        return self.return_report_recruitment(report_name)

    @api.multi
    def return_report_recruitment(self, report_name):
        param_obj = self.env['ir.config_parameter']
        url = param_obj.get_param('report_recruitment')
        if url == False:
            raise ValidationError(_(u"Bạn phải cấu hình birt_url"))
        recruitment = '0'
        if self.recruitment_session_id:
            for a in self.recruitment_session_id:
                recruitment += ', ' + str(a.id)
        return {
            'type': 'ir.actions.act_url',
            'url': url + "report/frameset?__report=report_vmt/" + report_name + "&recruitment_session_id=" + recruitment,
            'target': 'new',
            }

    @api.multi
    def return_report_recruitment_applicant(self, report_name):
        param_obj = self.env['ir.config_parameter']
        url = param_obj.get_param('report_recruitment')
        if url == False:
            raise ValidationError(_(u"Bạn phải cấu hình birt_url"))
        recruitment = '0'
        if self.recruitment_session_id:
            for a in self.recruitment_session_id:
                recruitment += ', ' + str(a.id)
        if self.job_applicant_id:
            department = str(self.job_applicant_id.id)
        else:
            department = '0'
        return {
            'type': 'ir.actions.act_url',
            'url': url + "report/frameset?__report=report_vmt/" + report_name + "&recruitment_session_id=" + recruitment + "&department_id=" + department,
            'target': 'new',
            }