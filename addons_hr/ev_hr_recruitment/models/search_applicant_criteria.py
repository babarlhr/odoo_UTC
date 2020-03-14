# -*- coding: utf-8 -*-
from odoo import fields, models, api
from odoo.exceptions import except_orm


class search_applicant_criteria(models.TransientModel):
    _name = 'hr.search.applicant.criteria'

    partner_name = fields.Char(string='Name')
    applicant_phone = fields.Char(string="applicant phone")
    applicant_email = fields.Char(string="applicant email")
    certificates = fields.Char(string="Certificate", help='Nhập chuyên ngành của chứng chỉ theo dạng: ví dụA, ví dụ B, ...')
    job_position_id = fields.Many2one('hr.job.position', string="Job position")
    year_of_birth = fields.Char(string="Year of birth")

    search_applicant_result_ids = fields.One2many('hr.search.applicant.result','search_applicant_criteria_id', string="Results", readonly=True)

    @api.multi
    def action_search_applicant(self):
        self.search_applicant_result_ids.unlink()
        query = """
                SELECT a.id,a.name,a.partner_name,a.applicant_email,a.applicant_phone,a.status_applicant
                FROM hr_applicant a
                LEFT JOIN hr_certificate b ON b.applicant_id = a.id
                WHERE 1=1
                """
        condition = ""
        condition_param = []

        if self.partner_name and len(self.partner_name.strip()):
            condition += " AND a.partner_name ilike %s "
            condition_param.append('%'+self.partner_name.strip()+'%')

        if self.applicant_phone and len(self.applicant_phone.strip()):
            condition += " AND a.applicant_phone ilike %s "
            condition_param.append('%'+self.applicant_phone.strip()+'%')

        if self.applicant_email and len(self.applicant_email.strip()):
            condition += " AND a.applicant_email ilike %s "
            condition_param.append('%'+self.applicant_email.strip()+'%')

        if self.certificates:
            certificates = '\'\''
            for c in self.certificates.strip().lower().split(','):
                certificates += ',\'' + c.strip() + '\''
            condition += " AND lower(b.major) in (" + certificates +") "

        if self.job_position_id:
            condition += " AND job_position_id = %s "
            condition_param.append(self.job_position_id.id)

        if self.year_of_birth > 0:
            condition += " AND to_char(a.date_of_birth, 'YYYY') ilike %s::text "
            condition_param.append(self.year_of_birth.strip())

        condition += ' GROUP BY a.id,a.name,a.partner_name,a.applicant_email,a.applicant_phone,a.status_applicant '
        condition_params = tuple(condition_param)
        q = query + condition

        self._cr.execute(q, condition_params)
        res_line = self._cr.dictfetchall()
        # print("res_line: " + str(res_line))
        print("query: " + str(q.encode('utf-8')))
        search_applicant_result_obj = self.env['hr.search.applicant.result']

        if res_line and len(res_line) > 0:
            for res in res_line:
                search_applicant_result_obj.create({
                    'applicant_id': res['id'],
                    'name': res['name'],
                    'partner_name': res['partner_name'],
                    'applicant_email': res['applicant_email'],
                    'applicant_phone': res['applicant_phone'],
                    'status_applicant': res['status_applicant'],
                    'search_applicant_criteria_id': self.id,
                })

        else:
            raise except_orm('Thông báo', 'Không tìm thấy ứng viên')


