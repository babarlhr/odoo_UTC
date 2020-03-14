# -*- coding: utf-8 -*-
import itertools

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, except_orm

STATE_REQUEST_SELECTION = [
    ('draft', 'Draft'),
    ('pending', 'Pending'),
    ('process', 'Process'),
    ('done', 'Done'),
    ('cancel', 'Cancel')
]

class recruitment_request(models.Model):
    _name = 'hr.recruitment.request'
    _order = 'id desc'

    # default method 'department_request'
    def _get_department_login(self):

        employee_id = self.get_employee_from_user()
        employee = self.env['hr.employee'].browse(employee_id)
        if employee.department_id:
            return employee.department_id
        else:
            raise except_orm(_('Thông báo'),_('Bạn không thuộc phòng ban nào, vui lòng liên hệ quản trị viên để được giải quyết!'))

    def get_employee_from_user(self):
        query = "select a.id from hr_employee a, resource_resource b where a.user_id = %s and b.user_id = %s"
        self._cr.execute(query, (self.env.user.id,self.env.user.id))
        res = self._cr.dictfetchone()
        if res:
            return res['id']

    # Master data
    name = fields.Char(string="Name")
    department_id = fields.Many2one('hr.department', string="Department", default=_get_department_login)
    request_date = fields.Date(string="Request date", required=True)
    reponse_date = fields.Date(string="Response date", required=True)
    note = fields.Text(string="Note")

    # Detail Data
    recruitment_request_line_ids = fields.One2many('hr.recruitment.request.line', 'recruitment_request_id', string="Recruitment request line")

    # state recruitment_request
    state = fields.Selection(STATE_REQUEST_SELECTION, default='draft')

    @api.multi
    def send(self):
        if len(self.recruitment_request_line_ids) > 0 and self.department_id:
            cr = self._cr

            job_id_ids = ''
            # job_position_ids = ''
            for recruitment_request_line in self.recruitment_request_line_ids:
                job_id_ids += str(recruitment_request_line.job_id.id) + ','
                # job_position_ids += str(recruitment_request_line.job_position_id.id) + ','
            job_id_ids += '0'
            # job_position_ids += '0'

            query = """
                    SELECT a.id,c.name job_id,d.name job_position
                    FROM hr_recruitment_request_line a
                    INNER JOIN hr_job c ON c.id = a.job_id
                    INNER JOIN hr_job_position d ON d.id = a.job_position_id
                    WHERE a.recruitment_request_id in (
                        SELECT b.id FROM hr_recruitment_request b
                        WHERE b.department_id = %s
                            AND b.state in ('pending','process')
                    )
                        AND a.job_id = ANY( string_to_array(%s, ',')::integer[])

                    """
                        # AND a.job_position_id = ANY( string_to_array(%s, ',')::integer[])
            param = (self.department_id.id ,str(job_id_ids),)
            cr.execute(query, param)
            res = cr.dictfetchall()
            if len(res) > 0:
                job_id = ''
                # job_position = ''
                for r in res:
                    job_id = str(r['job_id'].encode('utf-8'))
                    # job_position = str(r['job_position'].encode('utf-8'))
                    break
                raise except_orm(_('Thông báo'),_('Vui lòng chờ yêu cầu tuyển dụng chức danh ' + job_id + ' của yêu cầu trước đó kết thúc!'))
            else:
                self.state = 'pending'
        else:
            raise except_orm(_('Thông báo'),_('Bạn chưa nhập các vị trí cần tuyển dụng!'))

    @api.multi
    def receive(self):
        self.state = 'process'

    @api.multi
    def cancel(self):
        self.state = 'cancel'

    @api.multi
    def done(self):
        self.state = 'done'
        for recruitment_request_line in self.recruitment_request_line_ids:
            if recruitment_request_line.status_request == 'process':
                raise except_orm(_('Thông báo'), _('Chưa cập nhật trạng thái cho các vị trí tuyển dụng!'))
                break

    @api.onchange('reponse_date')
    def onchange_reponse_date(self):
        res = {}
        if self.request_date and self.request_date > self.reponse_date:
            res = {'warning': {
                        'title': _('Warning'),
                        'message': _('Request date \'' + str(self.request_date) + '\' must be less than Reponse date \'' + str(self.reponse_date) + '\' .')
                        }
            }
        if res:
            return res

    @api.onchange('request_date')
    def onchange_request_date(self):
        res = {}
        if self.reponse_date and self.request_date > self.reponse_date:
            res = {'warning': {
                        'title': _('Warning'),
                        'message': _('Request date \'' + str(self.request_date) + '\' must be less than Reponse date \'' + str(self.reponse_date) + '\' .')
                        }
            }
        if res:
            return res

    @api.constrains('reponse_date', 'request_date')
    def _check_time_get_profile(self):

        if self.request_date > self.reponse_date:
            raise ValidationError('Request date \'' + str(self.request_date) + '\' must be less than Reponse date \'' + str(self.reponse_date) + '\' .')

    @api.constrains('department_id')
    def _check_department_id(self):
        if not self.department_id:
            raise except_orm(_('Thông báo'),_('Bạn không thuộc phòng ban nào, vui lòng liên hệ quản trị viên để được giải quyết!'))

    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code('hr_recruitment_request_name_seq')
        return super(recruitment_request, self).create(vals)

