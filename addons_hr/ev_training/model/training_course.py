# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import except_orm

class training_course(models.Model):
    _name = 'training.course'

    name = fields.Char(string='Course')
    code = fields.Char(string=_('Code'), help=_('The code will be generated automatically'), select=True,
                             default='/', readonly=False, required=True)
    start_date = fields.Date(string='Start date')
    end_date = fields.Date(string='End date')
    description = fields.Text(string='Descripton')
    target = fields.Char(string='Target')  # mục tiêu
    session_ids = fields.One2many('training.session', 'course_id', string='Session')
    state = fields.Selection(selection=(('new', 'New'), ('active', 'Active'), ('done', 'Done')), default='new')
    department_ids = fields.Many2many('hr.department', string='Department') #bộ phận áp dụng

    @api.onchange('end_date')
    def onchange_end_date(self):
        if self.end_date and self.start_date:
            if self.end_date[0:10] < self.start_date[0:10]:
                self.end_date = False
                self.start_date = False
                return {'warning': {
                    'title': _('Thông báo'),
                    'message': _('"Ngày bắt đầu" phải nhỏ hơn "Ngày kết thúc". Vui lòng chọn lại!')
                }
                }

    @api.multi
    def action_active(self):
        self.state = 'active'

    @api.multi
    def action_done(self):
        if self.session_ids:
            for s in self.session_ids:
                if s.state != 'done':
                    raise except_orm(_('Phát hiện sai'),
                                     _('Không được phép kết thúc khóa đào tạo khi các lớp chưa kết thúc'))
        self.state = 'done'



    def _generate_code(self, sequence_code):
        sequence = self.pool('ir.sequence').get(self.env.cr, self.env.uid, sequence_code)
        code = str(sequence)
        return code


    @api.model
    def create(self, vals):
        if vals.get('website'):
            vals['website'] = self._clean_website(vals['website'])
        if vals.get('code', '/') == '/':
            vals['code'] = self._generate_code('ev_training_course_name_seq')
        return super(training_course, self).create(vals)




