# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import except_orm


class training_session_contest(models.Model):
    _name = 'training.session.contest'

    date = fields.Date(string='Date')
    major_id = fields.Many2one('training.major', string='Major')
    session_id = fields.Many2one('training.session', string='Session', domain=[('state','!=','new')])
    state = fields.Selection(selection=(('new', 'New'), ('active', 'Active'), ('done', 'Done')), default='new')
    line_ids = fields.One2many('training.session.contest.line', 'contest_id', string='Line')

    teacher_id = fields.Many2one('training.teacher', string='Teacher')

    @api.onchange('major_id','session_id')
    def onchange_major_id_session_id(self):
        if self.major_id and self.session_id :
            major_id = self.major_id.id
            is_in = False
            for item in self.session_id.timetable_ids:
                if item.major_id:
                    if major_id == item.major_id.id:
                        is_in = True
                        break
            if not is_in:
                raise except_orm('Thông báo', 'Môn học phải thuộc lớp học')

    @api.onchange('date')
    def onchange_date(self):
        if self.date and self.session_id.start_date and self.session_id.end_date:
            if self.session_id.start_date > self.date or self.session_id.end_date < self.date:
                raise except_orm('Thông báo', 'Ngày thi phải thuộc ngày lớp học hoạt động')

    @api.multi
    def action_active(self):
        if self.session_id:
            if self.session_id.state == 'new':
                raise except_orm('Thông báo', 'Lớp này chưa hoạt động')
        self.state = 'active'



    @api.onchange('session_id')
    def onchage_session_id(self):
        if self.session_id:
            list = []
            for pt_contest in self.session_id.employees_ids:
                list.append({
                    'employee_id': pt_contest.employee_id.id,
                    'line_ids': self.id
                    })
                self.line_ids = list

    @api.multi
    def done(self):
        # if self.line_ids:
        #     for a in self.line_ids:
        #         if a.rating == False:
        #             raise except_orm('Thông báo', 'Không được kết thúc khi chưa đánh giá hết học viên')
        self.state = 'done'

    @api.model
    def default_get(self, fields):

        res = super(training_session_contest, self).default_get(fields)

        # print("self._context: " + str(self._context))
        context = self._context
        if context and 'training_session_id' in context:
            res['session_id'] = context['training_session_id']
        return res

class training_session_contest_line(models.Model):
    _name = 'training.session.contest.line'

    scores = fields.Integer(string='Scores')
    # Điểm thưc hành thêm ngày 26/8
    practice_scores = fields.Float(string='Practice scores')
    # Điểm lý thuyết thêm ngày 26/8
    theory_scores = fields.Float(string='Theory Scores')
    contest_id = fields.Many2one('training.session.contest', string='Contest')
    employee_id = fields.Many2one('hr.employee', string='Employee')
    rating_ids = fields.Many2many('training.rating', string='Rating')
    # Ưu điểm thêm ngày 26/8
    advantages = fields.Text(string='Advantages', )
    # Nhược điểm
    defect = fields.Text(string='Defect', )
    # ý kiến bổ sung
    additional_comments = fields.Text(string='Additional comments', )
    # Khả năng
    ability  = fields.Text(string='Ability ', )
    type = fields.Selection(string="Type", selection=[('exam', 'Exam'), ('notexam', 'Not Exam'), ], required=False, )







