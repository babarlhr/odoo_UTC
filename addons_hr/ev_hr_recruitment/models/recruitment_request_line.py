# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import except_orm

STATUS_REQUEST_SELECTION = [
    ('process', 'Process'),
    ('enough', 'Enough'),
    ('not_enough', 'Not enough')
]

class recruitment_request_line(models.Model):
    _name = 'hr.recruitment.request.line'
    _order = 'id desc'

    job_id = fields.Many2one('hr.job', string="Job title", required=True)
    job_position_id = fields.Many2one('hr.job.position', string="Job position", required=True)
    qty = fields.Integer(string="Quantity", default=0)
    actual_qty = fields.Integer(string="The actual quantity", default=0)
    description = fields.Text(string="Description")
    status_request = fields.Selection(STATUS_REQUEST_SELECTION, 'Status request', default='process')
    recruitment_request_id = fields.Many2one('hr.recruitment.request', string="Recruitment request",  ondelete='cascade')
    recruitment_request_state = fields.Selection(related='recruitment_request_id.state', readonly=True)

    @api.onchange('job_id')
    def onchange_job_id(self):
        job_id = self.env['hr.applicant'].search([('job_id', '=', self.job_id.id)])
        self.actual_qty = len(job_id)

    @api.onchange('actual_qty')
    def onchange_actual_qty(self):
        print("self.status_request before: " + str(self.status_request))
        if self.qty != 0:
            if self.actual_qty < self.qty:
                self.status_request = 'not_enough'
            else:
                self.status_request = 'enough'

        print("self.status_request after: " + str(self.status_request))

    @api.multi
    def action_open_form_update_request_line(self):
        return {
            'name': ('Cập nhật chi tiết'),
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'hr.recruitment.request.line',
            'view_id': False,
            'res_id': self.id,
            'type': 'ir.actions.act_window',
            'target':'new'
        }

    @api.multi
    def action_update_request_line(self):
        return True

    @api.constrains('qty',)
    def _check_qty(self):
        if self.qty <= 0:
            raise except_orm(_('Thông báo'), _('Số lượng nhập lớn hơn 0. Vui lòng nhập lại số lượng.'))