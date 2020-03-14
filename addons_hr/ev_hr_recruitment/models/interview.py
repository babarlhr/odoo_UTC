# -*- coding: utf-8 -*-
from datetime import date
# from xml import etree
# from pip._vendor.html5lib.treewalkers import etree
# from pip._vendor.html5lib.treebuilders import etree
from lxml import etree
from odoo import fields, api, models, _
from odoo.exceptions import except_orm, ValidationError, MissingError

STATE_INTERVIEW_SELECTION = [
    ('draft', 'Draft'),
    ('invite', 'Invite'),
    ('process', 'Process'),
    ('done', 'Done'),
    ('cancel', 'Cancel'),
]


class interview(models.Model):
    _name = 'hr.interview'

    name = fields.Char(string="Name")
    recruitment_session_id = fields.Many2one('hr.recruitment.session', string="Recruitment session", required=True)
    interviewer_ids = fields.Many2many('hr.employee', string="Interviewer", create_edit=False, required=True)
    from_date_interview = fields.Date(string="From date", required=True)
    to_date_interview = fields.Date(string="To date", required=True)
    note = fields.Text(string="Note")
    times_interview = fields.Integer(string="Times interview")
    job_id = fields.Many2one('hr.job', string='Job')
    interview_line_ids = fields.One2many('hr.interview.line', 'interview_id', string="Detail", required=True)
    state = fields.Selection(STATE_INTERVIEW_SELECTION, default='draft', string="State interview")

    @api.multi
    def start(self):
        print("interview.py > def start")
        if len(self.interview_line_ids) > 0:
            self.state = 'invite'
        else:
            raise except_orm(_('Thông báo'), _('Không thể khởi động khi chưa có ứng viên, mời thêm ứng viên!'))


    @api.multi
    def done(self):
        print("interview.py > def done")
        self.state = 'done'
        is_interviewer = False
        cr = self._cr
        employee_ids = ''
        for employee_id in self.interviewer_ids:
            employee_ids += str(employee_id.id) + ','
        employee_ids += '0'
        query = """ SELECT RR.user_id FROM resource_resource RR
                    INNER JOIN hr_employee HE ON RR.id = HE.resource_id WHERE HE.id = ANY( string_to_array(%s, ',')::integer[]) """
        param = (str(employee_ids),)
        cr.execute(query, param)
        res = cr.dictfetchall()
        for user_id in res:
            if self._uid == user_id['user_id']:
                is_interviewer = True
                break

        if is_interviewer:
            for interview_line in self.interview_line_ids:
                if interview_line.status_applicant == 'waiting':
                    raise except_orm(_('Thông báo'), _('Chưa cập nhất hết kết quả cho ứng viên.'))
                    break
        else:
            raise except_orm(_('Thông báo'),
                             _('Bạn không phải là người phỏng vấn nên không thể kết thúc đợt phỏng vấn này.'))

    @api.multi
    def cancel(self):
        print("interview.py > def cancel")
        self.state = 'cancel'

    @api.onchange('to_date_interview')
    def onchange_to_date_interview(self):
        print("interview.py > def onchange_to_date_interview")
        res = {}
        if self.from_date_interview and self.from_date_interview > self.to_date_interview:
            res = {'warning': {
                'title': _('Warning'),
                'message': _('From date \'' + str(self.from_date_interview) + '\' must be less than To date \'' + str(
                    self.to_date_interview) + '\' .')
            }
            }
        if res:
            return res
    @api.constrains('job_id','recruitment_session_id')
    def onchange_job_id(self):
        list_job = []

        for r in  self.recruitment_session_id.recruitment_session_line_ids:
            list_job.append(r.job_id.id)

        if self.job_id.id not in list_job:
            raise except_orm(_('Thông báo'),
                             _('Chức danh này không có trong đợt phỏng vấn. Vui lòng chọn lại !!!!!'))


    @api.onchange('from_date_interview')
    def onchange_from_date_interview(self):
        res = {}
        if self.from_date_interview and self.from_date_interview < self.recruitment_session_id.time_start_receive_resumes:
            raise except_orm(_('Thông báo'),_('Ngày bắt đầu phỏng vấn phải sau ngày bắt đầu đợt tuyển dụng.'))

        if self.recruitment_session_id and self.from_date_interview:
            _interview = self.search([('recruitment_session_id','=',self.recruitment_session_id.id)], order='to_date_interview desc')
            if _interview:
                if _interview[0].to_date_interview > self.from_date_interview:
                    self.from_date_interview = False
                    res = {'warning': {
                        'title': _('Warning'),
                        'message': _('Đợt phỏng vấn sau phải có thời gian sau đợt phỏng vấn trước, mời chọn lại!')}
                    }

        if self.to_date_interview and self.from_date_interview > self.to_date_interview:
            res = {'warning': {
                'title': _('Warning'),
                'message': _('From date \'' + str(self.from_date_interview) + '\' must be less than To date \'' + str(
                    self.to_date_interview) + '\' .')
            }
            }
        if res:
            return res

    @api.onchange('recruitment_session_id', 'job_id')
    def onchange_recruitment_session_job(self):
        print("interview.py > def onchange_recruitment_session")
        if self.recruitment_session_id and self.from_date_interview:
            _interview = self.search([('recruitment_session_id','=',self.recruitment_session_id.id)], order='to_date_interview desc')
            if _interview:
                if _interview[0].to_date_interview > self.from_date_interview:
                    self.from_date_interview = False
                    res = {'warning': {
                        'title': _('Warning'),
                        'message': _('Đợt phỏng vấn sau phải có thời gian sau đợt phỏng vấn trước, mời chọn lại!')}
                    }
                    return res

        if self.recruitment_session_id and self.job_id:
            list_interview = self.search([('recruitment_session_id', '=', self.recruitment_session_id.id),('job_id', '=', self.job_id.id), ('state', '!=', 'cancel')],
                                         order="id asc")

            if list_interview:
                previous_interview = list_interview[(len(list_interview) - 1)]
                times_previous_interview = previous_interview.times_interview

                self.times_interview = times_previous_interview + 1

    @api.onchange('interview_line_ids')
    def onchange_interview_line(self):
        print("interview.py > def onchange_interview_line")
        count_interview_line_ids = len(self.interview_line_ids)
        if count_interview_line_ids > 0:
            applicant_id_new = self.interview_line_ids[count_interview_line_ids - 1].applicant_id
            i = 0
            for interview_line in self.interview_line_ids:
                i += 1
                if i == count_interview_line_ids:
                    break
                else:
                    if interview_line.applicant_id.id == applicant_id_new.id:
                        raise except_orm(_('Thông báo'), _('Không được chọn trùng ứng viên.'))
                        break

    @api.multi
    def action_send_mail_invite_interview(self):
        if self.state == 'draft':
            raise except_orm(_('Thông báo'), _('Bạn chưa gửi lời mời phóng vấn đến các ứng viên, hãy bấm vào nút khởi động.'))
        # model, view_id = self.pool['ir.model.data'].get_object_reference(self._cr, self._uid, 'ev_hr_recruitment',
        #                                                        'list_send_mail_applicant_interview_form')
        view_id = self.env.ref('ev_hr_recruitment.list_send_mail_applicant_interview_form', False)
        template = self.env['ir.model.data'].sudo().get_object('ev_hr_recruitment',
                                                               'template_hr_recruitment_send_mail_invite_interview_form')

        print(template.body_html)

        return {
            'name': _('List Applicant'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'list.send.mail.applicant.interview',
            'views': [(view_id.id, 'form')],
            'view_id': view_id.id,
            'target': 'new',
            'context': {'default_interview_id': self.id,
                               'default_body_html': template.body_html}
        }



    @api.constrains('to_date_interview', 'from_date_interview')
    def _check_interview_time(self):
        print("interview.py > def _check_interview_time")
        if self.from_date_interview > self.to_date_interview:
            raise ValidationError(
                'From date \'' + str(self.from_date_interview) + '\' must be less than To date \'' + str(
                    self.to_date_interview) + '\' .')

    @api.constrains('recruitment_session_id', )
    def _check_times_intervew(self):
        print("interview.py > def _check_times_intervew")
        list_interview = self.search(
            [('recruitment_session_id', '=', self.recruitment_session_id.id), ('id', '!=', self.id)], order="id asc")
        if list_interview:
            to_date_previous_interview = list_interview[(len(list_interview) - 1)].to_date_interview
            if self.from_date_interview < to_date_previous_interview:
                raise ValidationError('Start date must interview after the end of the previous interview')

    @api.model
    def default_get(self, fields):
        print("interview.py > def default_get")
        print("self._context: " + str(self._context))
        previous_interview = self._context.get('previous_interview', False)
        interview_ids = self._context.get('interview_ids', False)
        res = super(interview, self).default_get(fields)
        if previous_interview:
            previous_interview_id = [int(previous_interview)][0]
            previous_interview = self.pool['hr.interview'].browse(self._cr, self._uid, previous_interview_id)
            res.update({'name': previous_interview.name})
            res.update({'recruitment_session_id': previous_interview.recruitment_session_id.id})
            for interview_line in previous_interview.interview_line_ids:
                if interview_line.status_applicant == 'pass':
                    print("interview_line.status_applicant: " + interview_line.status_applicant)
                    arr_interview_line = {'applicant_id': interview_line.applicant_id.id, }
                    res.update({'interview_line_ids': [(0, 0, arr_interview_line)]})
        elif interview_ids:
            res.update({'times_interview': len(interview_ids) + 1})
        return res

    @api.model
    def create(self, vals):
        print("interview.py > def create")
        vals['name'] = self.pool.get('ir.sequence').next_by_code(self.env.cr, self.env.uid, 'hr_interview_name_seq')
        new = super(interview, self).create(vals)

        list_interview = self.env['hr.interview'].search(
            [('recruitment_session_id', '=', new.recruitment_session_id.id),('job_id', '=', new.job_id.id), ('id', '!=', int(new.id))], order="id asc")
        if list_interview:
            previous_interview = list_interview[(len(list_interview) - 1)]
            times_previous_interview = previous_interview.times_interview

            new.times_interview = times_previous_interview + 1

        else:
            new.times_interview = 1

        return new

    # def fields_view_get(self, cr, uid, view_id=None, view_type=False, context=None, toolbar=False, submenu=False):
    #     # env = api.Environment(cr, uid, {})
    #     # obj_ir_ui_view = env['ir.ui.view']
    #     # obj_hr_interview = env['hr.interview']
    #
    #     print("<<<<<<<<<<<<<<<")
    #     print("context: " + str(context))
    #     print("view_id: " + str(view_id))
    #     print(">>>>>>>>>>>>>>>")
    #     if context is None:
    #         context = {}
    #     res = super(interview, self).fields_view_get(cr, uid, view_id, view_type, context, toolbar, submenu)
    #     # if view_type == 'form':
    #     #     # print("<<<<<<<<<<<<<<<")
    #     #     # print("context: " + str(context))
    #     #     # print("view_id: " + str(view_id))
    #     #     # print(">>>>>>>>>>>>>>>")
    #     #     # obj_hr_interview.search([('id', '=', context['params'][''])])
    #     #
    #     #     view_obj = obj_ir_ui_view.search([('id', '=', view_id)])
    #     #     view_dom = etree.XML(view_obj[0]['arch'])
    #     #     for node in view_dom.xpath("//button[@name='action_send_mail_invite_work']"):
    #     #         node.set('invisible', "True")
    #     #     xarch, xfields = self._view_look_dom_arch(cr, uid, view_dom, view_id, context=context)
    #     #     res['arch'] = xarch
    #     #     res['fields'] = xfields
    #     return res

    # def fields_view_get(self, cr, uid, view_id=None, view_type=False, context=None, toolbar=False, submenu=False):
    #     if context is None:
    #         context = {}
    #     res = super(interview, self).fields_view_get(cr, uid, view_id, view_type, context, toolbar, submenu)
    #     mod_obj = self.pool.get('ir.model.data')
    #     dummy, except_view_id = tuple(mod_obj.get_object_reference(cr, uid, 'ev_hr_recruitment', "view_interview_form"))
    #     print("view_id: " + str(view_id))
    #     print("context: " + str(context))
    #     print("dummy: " + str(dummy))
    #     print("except_view_id: " + str(except_view_id))
    #     #
    #     # if view_type == 'tree':
    #     #     doc = etree.XML(res['arch'])
    #     #
    #     #     if view_id != except_view_id:
    #     #         for node in doc.xpath("//field[@name='location_id']"):
    #     #             node.set('invisible', "True")
    #     #         for node in doc.xpath("//field[@name='location_dest_id']"):
    #     #             node.set('invisible', "True")
    #     #
    #     #     for node in doc.xpath("//field[@name='date_expected']"):
    #     #         node.set('invisible', "True")
    #     #
    #     #     location_dest_id = context.get('default_location_dest_id', False)
    #     #     if location_dest_id:
    #     #         location_dest = self.pool.get('stock.location').browse(cr, uid, location_dest_id)
    #     #         if location_dest.usage in ['supplier', 'customer']:
    #     #             for node in doc.xpath("//field[@name='price_unit']"):
    #     #                 node.set('invisible', "True")
    #     #             for node in doc.xpath("//field[@name='price_subtotal']"):
    #     #                 node.set('invisible', "True")
    #     #             for node in doc.xpath("//field[@name='is_promotion']"):
    #     #                 node.set('invisible', "True")
    #     #
    #     #             for node in doc.xpath("//field[@name='sale_price_unit']"):
    #     #                 node.set('invisible', "False")
    #     #             for node in doc.xpath("//field[@name='sale_price_subtotal']"):
    #     #                 node.set('invisible', "False")
    #     #
    #     #     xarch, xfields = self._view_look_dom_arch(cr, uid, doc, view_id, context=context)