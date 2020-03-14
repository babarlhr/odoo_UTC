# -*- coding: utf-8 -*-
from datetime import datetime, date, timedelta
import requests
from odoo import fields, models, api, _

STATUS_RECRUITMENT_SELECTION = [
    ('apply', 'Apply'),
    ('complete_profile', 'Complete profile'),
    ('withdrawal_profile', 'Withdrawal profile'),
    ('accepted', 'Accepted'),
    ('training', 'Training'),
    ('trained', 'Trained'),
]

STATUS_APPLICANT_SELECTION = [
    ('not_employee', 'Not employee'),
    ('is_employee', 'Is employee'),
]

GENDER_SELECTION = [
    ('NA', 'Male'),
    ('NU', 'Female'),
    ('KH', 'Other'),
]

PROVINCE_SELECTION = [
    ('HNI', 'Hà Nội'),
    ('HCM', 'Hồ Chí Minh'),
    ('HPG', 'Hải Phòng'),
    ('AGG', 'An Giang'),
    ('BDG', 'Bình Dương'),
    ('BDH', 'Bình Ðịnh'),
    ('BGG', 'Băc Giang'),
    ('BKN', 'Băc Kạn'),
    ('BLU', 'Bạc Liêu'),
    ('BNH', 'Bắc Ninh'),
    ('BPC', 'Bình Phước'),
    ('BTE', 'Bến Tre'),
    ('BTN', 'Bình Thuận'),
    ('CBG', 'Cao Bằng'),
    ('CMU', 'Cà Mau'),
    ('CTO', 'Cần Thơ'),
    ('DBN', 'Ðiện Biên'),
    ('DCN', 'Ðak Nông'),
    ('DLK', 'Ðak Lak'),
    ('DNG', 'Đà Nẵng'),
    ('DNI', 'Ðồng Nai'),
    ('DTP', 'Ðồng Tháp'),
    ('GLI', 'Gia Lai'),
    ('HBH', 'Hòa Bình'),
    ('HDG', 'Hải Dương'),
    ('HGG', 'Hà Giang'),
    ('HNM', 'Hà Nam'),
    ('HTH', 'Hà Tinh'),
    ('HUE', 'Huế'),
    ('HUG', 'Hậu Giang'),
    ('HYN', 'Hưng Yên'),
    ('KGG', 'Kiên Giang'),
    ('KHA', 'Khánh Hòa'),
    ('KTM', 'Kon Tum'),
    ('LAN', 'Long An'),
    ('LCI', 'Lào Cai'),
    ('LCU', 'Lai Châu'),
    ('LDG', 'Lâm Ðồng'),
    ('LSN', 'Lạng Sơn'),
    ('NAN', 'Nghệ An'),
    ('NBH', 'Ninh Bình'),
    ('NDH', 'Nam Ðịnh'),
    ('NTN', 'Ninh Thuận'),
    ('PTO', 'Phú Thọ'),
    ('PYN', 'Phú Yên'),
    ('QBH', 'Quảng Bình'),
    ('QNH', 'Quảng Ninh'),
    ('QNI', 'Quảng Ngãi'),
    ('QNM', 'Quảng Nam'),
    ('QTI', 'Quảng Trị'),
    ('SLA', 'Sơn La'),
    ('STG', 'Sóc Trăng'),
    ('TBH', 'Thái Bình'),
    ('TGG', 'Tiền Giang'),
    ('THA', 'Thanh Hóa'),
    ('TNH', 'Tây Ninh'),
    ('TNN', 'Thái Nguyên'),
    ('TQG', 'Tuyên Quang'),
    ('TVH', 'Trà Vinh'),
    ('VLG', 'Vĩnh Long'),
    ('VPC', 'Vĩnh Phúc'),
    ('VTU', 'Vũng Tàu'),
    ('YBI', 'Yên Bái'),

]


class applicant(models.Model):
    _inherit = 'hr.applicant'
    _order = 'create_date DESC'

    name = fields.Char(string="Subject / Application Name", required=False)
    partner_name = fields.Char(string="Applicant's Name", required=True)
    avatar = fields.Binary('Avatar',
                           help="This field holds the image used as photo for the applicant, limited to 1024x1024px.")

    place_of_birth = fields.Selection(PROVINCE_SELECTION, string="Place of birth")
    date_of_birth = fields.Date(string="Date of birth")
    gender = fields.Selection(GENDER_SELECTION, default='NU', required=True)
    height = fields.Char(string="Height")
    weight = fields.Char(string="Weight")
    address = fields.Char(string="Address")
    current_address = fields.Char(string="Current address")
    identity_card = fields.Char(string="Identity Card", )
    place_of_issue = fields.Selection(PROVINCE_SELECTION, string="Place of Issue", )
    date_of_issue = fields.Date(string="Date of Issue", )
    applicant_phone = fields.Char(string="applicant phone", required=True)
    applicant_email = fields.Char(string="applicant email")
    account_facebook = fields.Char(string="Account facebook")
    is_recruited = fields.Boolean(string="Is recruited")
    description_recruited = fields.Text(string="Description recruited")

    job_id = fields.Many2one('hr.job', string="Job title")
    job_position_id = fields.Many2one('hr.job.position', string="Job position")
    recent_income = fields.Char(string="Recent income")
    expected_income = fields.Char(string="Expected income")
    plan_date = fields.Date(string="Plan date")

    receiver_id = fields.Many2one('hr.employee', string="Receiver")

    file_cv = fields.Binary('File CV')
    file_cv_name = fields.Char('File CV Name')

    certificate_ids = fields.One2many('hr.certificate', 'applicant_id', string="Certificate")
    experience_ids = fields.One2many('hr.experience', 'applicant_id', string="Experience")

    advantage = fields.Text('Advantage')
    disadvantages = fields.Text('Disadvantages')
    hobby = fields.Text(string="Hobby")

    applicant_references_ids = fields.One2many('hr.applicant.references', 'applicant_id', string="References")
    applicant_degree_ids = fields.One2many('hr.applicant.degree', 'applicant_id', string="Degree")
    foreign_language_ids = fields.One2many('hr.foreign.language', 'applicant_id', string="Foreign language")
    family_relationship_ids = fields.One2many('hr.family.relationship', 'applicant_id', string="Family relationship")
    is_married = fields.Boolean(string="Is married")
    informatics = fields.Char(string="Informatics")
    compatibility_with_positive_position = fields.Char(string="Compatibility with positive position")
    other_courses = fields.Text(string="Other courses")
    applicant_source_id = fields.Many2one('hr.applicant.source', string="Applicant source")
    status_applicant = fields.Selection(STATUS_APPLICANT_SELECTION, default='not_employee')
    other_source = fields.Char(string="Other source")
    # status_recruitment = fields.Selection(STATUS_RECRUITMENT_SELECTION, default="apply", string="Status recruitment")
    status_recruitment = fields.Many2one('hr.applicant.status', string="Status recruitment")
    work_place = fields.Many2one('res.country.state', string="Work place")
    note = fields.Text(string="Note")
    applicant_call_history = fields.One2many('hr.applicant.call.history', 'applicant_id',
                                             string="Applicant call history")
    experience = fields.Selection(selection=[('K', 'No'), ('1_year', '1 year'), ('over_1_year', 'Over 1 year')]
                              , default='') # kinh nghiệm làm việc

    #
    # file_cv_demo = fields.Many2one('ir.attachment', string='File CV demo')
    # file_cv_demo1 = fields.Binary(attachment=True, string='File CV demo1')


    @api.multi
    def action_print_cv(self):

        param_obj = self.pool.get('ir.config_parameter')
        url = param_obj.get_param(self._cr, self._uid, 'birt_url')
        # url = "http://192.168.0.158:8080"
        print(url)
        report_name = "report_cv_applicant.rptdesign"
        param_str = "&applicant_id=" + str(self.id)
        return {
            "type": "ir.actions.act_url",
            "url": url + "" + report_name + param_str,
            "target": "_parent"
        }

#     @api.model
#     def name_search(self, name='', args=None, operator='ilike', limit=100):
#         print("applycant.py > def name_search")
#         interview_id = self._context.get('interview_id')
#         context = self._context
#         print("applicant.py self._context: " + str(self._context))
#         if interview_id:
#             print(str(interview_id))
#             # if interview_id:
#             ids = []
#             obj_interview_line = '''SELECT applicant_id from hr_interview_line WHERE  interview_id = %s'''
#             self._cr.execute(obj_interview_line, (context['interview_id'],))
#             interview_line = self._cr.dictfetchall()
#             if interview_line and len(interview_line) > 0:
#                 for a in interview_line:
#                     ids.append(a['applicant_id'])
#             args.append(('id', 'in', ids))
#             res = super(applicant, self).name_search(name=name, args=args, operator=operator, limit=limit)
#
#
#         if 'recruitment_session_id_from_interview' in context and 'job_id' in context:
#             if context['recruitment_session_id_from_interview'] and context['job_id']:
#                 cr = self._cr
#                 query = '''select a.hr_applicant_id, b.partner_name,
# '[' || (SELECT status_applicant from  hr_interview c , hr_interview_line d
# where c.id = d.interview_id and c.recruitment_session_id = a.hr_recruitment_session_id and b.id = d.applicant_id limit 1) || ']' status_applicant
#  from hr_applicant_hr_recruitment_session_rel a, hr_applicant b
#                           where a.hr_recruitment_session_id=%s and a.hr_applicant_id = b.id and b.job_id = %s'''
#                 cr.execute(query, (context['recruitment_session_id_from_interview'],context['job_id']))
#                 applicants = cr.dictfetchall()
#                 result = []
#                 for a in applicants:
#                     status_applicant = ''
#                     if a['status_applicant']:
#                         status_applicant = a['status_applicant']
#                     result.append([a['hr_applicant_id'], a['partner_name'] + status_applicant])
#                 res = result
#             else:
#                 res = []
#         else:
#             res = super(applicant, self).name_search(name=name, args=args, operator=operator, limit=limit)
#         return res
#
#     def name_get(self, cr, uid, ids, context=None):
#         res = []
#         for a in self.browse(cr, uid, ids, context=context):
#
#             res.append([a.id, a.partner_name])
#         return res
#
#     def search(self, cr, uid, args, offset=0, limit=None, order=None, context=None, count=False):
#         recruitment_session_id = context.get('recruitment_session_id', False)
#         if recruitment_session_id:
#             query = """
#                 Select d.id
#                 from hr_applicant d
#                 where id not in(
#                             SELECT a.id FROM hr_applicant a where a.status_applicant = 'is_employee')
#                         and id not in
#                             (SELECT a.id
#                             FROM hr_applicant a
#                             INNER JOIN hr_applicant_hr_recruitment_session_rel b ON b.hr_applicant_id = a.id
#                             INNER JOIN hr_recruitment_session c ON c.id = b.hr_recruitment_session_id
#                             where c."state" <> 'done')
#                         and id not in
#                             (SELECT a.id
#                             FROM hr_applicant a
#                             INNER JOIN hr_applicant_hr_recruitment_session_rel b ON b.hr_applicant_id = a.id
#                             INNER JOIN hr_recruitment_session c ON c.id = b.hr_recruitment_session_id
#                             where c.id=%s )"""
#             cr.execute(query, (recruitment_session_id,))
#             res = cr.dictfetchall()
#             if len(res) > 0:
#                 ids = list(r['id'] for r in res)
#                 args.append((('id', 'in', ids)))
#             else:
#                 args.append((('id', '=', 0)))
#         return super(applicant, self).search(cr, uid, args, offset=offset, limit=limit, order=order,
#                                              context=context, count=count)
#
# # from odoo import osv, fields
# # from odoo import SUPERUSER_ID, tools
# #
# # class applicant_v1(osv.Model):
# #     _inherit = 'hr.applicant'
# #
# #     def _get_image(self, cr, uid, ids, name, args, context=None):
# #         result = dict.fromkeys(ids, False)
# #         for obj in self.browse(cr, uid, ids, context=context):
# #             result[obj.id] = {
# #                 'avatar_view': obj.avatar_attachment_id and obj.avatar_attachment_id.datas or None,
# #             }
# #         return result
# #
# #     def _set_image(self, cr, uid, id, name, value, args, context=None):
# #         obj = self.browse(cr, uid, id, context=context)
# #         avatar_view = obj.avatar_attachment_id.id
# #         if not value:
# #             ids = [attach_id for attach_id in [avatar_view] if attach_id]
# #             if ids:
# #                 self.pool['ir.attachment'].unlink(cr, uid, ids, context=context)
# #             return True
# #         if not (avatar_view):
# #             avatar_view = self.pool['ir.attachment'].create(cr, uid, {'name': 'avatar_view '}, context=context)
# #             self.write(cr, uid, id, {'avatar_attachment_id': avatar_view,},
# #                        context=context)
# #
# #         images = tools.image_get_resized_images(value, return_big=True, avoid_resize_medium=True)
# #         self.pool['ir.attachment'].write(cr, uid, avatar_view, {'datas': images['image']}, context=context)
# #
# #         return True
# #
# #     _columns = {
# #         'avatar_attachment_id': fields.many2one('ir.attachment', 'Avatar'),
# #
# #         'avatar_view': fields.function(_get_image, fnct_inv=_set_image, string="Avatar", multi='_get_image', type='binary',),
# #     }