# -*- coding: utf-8 -*-
import base64

import xlrd

from odoo import models, fields, api
from odoo.exceptions import except_orm
from odoo.tools.translate import _

from datetime import datetime


class import_applicant(models.TransientModel):
    _name = 'import.applicant'

    name = fields.Char(string='Name', default='Customer Update')
    file_upload = fields.Binary(string='File upload')
    file_name = fields.Char(string='File name')
    detail_ids = fields.One2many('import.applicant.detail', 'applicant_id', string='Applicant')
    state = fields.Selection([('draft', 'Draft'), ('done', 'Done')], default='draft')



    @api.multi
    def import_file_applicant(self):
        if not self.file_upload:
            raise except_orm('Thông báo', 'Bạn cần chọn file trước')
        """ Kiểm tra định dạng file """
        self.check_format_file_excel(self.file_name)
        data = self.file_upload  # tien hanh doc file
        data_file = base64.decodestring(data)
        excel = xlrd.open_workbook(file_contents=data_file)
        sheet = excel.sheet_by_index(0)
        print(sheet.nrows)
        self.detail_ids.unlink()

        try:
            if sheet:
                birthday_error = []
                create_date_error = []
                plan_date_error = []
                for rows in range(sheet.nrows):
                    if rows >= 1:
                        current_row = rows
                        birthday_check = sheet.cell_value(current_row, 1)
                        plan_date_check = sheet.cell_value(current_row, 10)
                        # create_date_check = sheet.cell_value(current_row, 12)
                        if birthday_check:
                            try:
                                xlrd.xldate_as_tuple(birthday_check, excel.datemode)
                            except:
                                birthday_error.append(str(current_row + 1))
                        # if create_date_check:
                        #     try:
                        #         xlrd.xldate_as_tuple(create_date_check, excel.datemode)
                        #     except:
                        #         create_date_error.append(str(current_row + 1))
                        if plan_date_check:
                            try:
                                xlrd.xldate_as_tuple(plan_date_check, excel.datemode)
                            except:
                                plan_date_error.append(str(current_row + 1))

                if birthday_error and len(birthday_error) > 0:
                    raise except_orm('Lỗi', ("Sai định dạng ngày sinh ở dòng: %s") % (','.join(birthday_error)))
                # if create_date_check and len(create_date_check) > 0:
                #     raise except_orm('Lỗi', ("Sai định dạng ngày có thể làm việc ở dòng: %s") % (','.join(create_date_error)))
                if plan_date_error and len(plan_date_error) > 0:
                    raise except_orm('Lỗi', ("Sai định dạng ngày nhận hồ sơ ở dòng: %s") % (','.join(plan_date_error)))
                for rows in range(sheet.nrows):
                    if rows >= 1:
                        current_row = rows
                        name_applicant = sheet.cell_value(current_row, 0) #tên ứng viên
                        birthday  = sheet.cell_value(current_row, 1) # ngày sinh
                        if birthday:
                            try:
                                if excel.datemode == 0 and 1.0 <= birthday < 61.0:
                                    raise except_orm('Lỗi', ("Hãy nhập ngày sinh >1900 ở dòng: %s") % ([
                                        (rows)]))
                                year, month, day, hour, min, second = xlrd.xldate_as_tuple(birthday, excel.datemode)
                                birthday_str = str(year) + "-" + str(month) + "-" + str(day)
                            except:
                                raise except_orm('Lỗi', ("Xem lại ngày sinh ở dòng: %s") % ([
                                    (rows)]))
                        else:
                            birthday_str = False
                        gender = sheet.cell_value(current_row, 2) # giới tính
                        if not gender:
                            raise except_orm('Lỗi', ("Thiếu thông tin giới tính ở dòng: %s") % ([
                                (rows)]))
                        phone = sheet.cell_value(current_row, 3) #sđt
                        if not phone:
                            raise except_orm('Lỗi', ("Thiếu số điện thoại ứng viên ở dòng: %s") % ([
                                (rows)]))
                        email = sheet.cell_value(current_row, 4) #email
                        account_facebook = sheet.cell_value(current_row, 5)
                        current_address = sheet.cell_value(current_row, 6) # nơi ở hiện tại
                        experience  = sheet.cell_value(current_row, 7) #kinh nghiệm đang để trong nguồn khác
                        job = sheet.cell_value(current_row, 8) # vị trí ứng tuyển
                        job_position = sheet.cell_value(current_row, 9) # ngành nghề tuyển dụng
                        plan_date = sheet.cell_value(current_row, 10) # ngày có thể làm việc
                        if plan_date:
                            try:
                                if excel.datemode == 0 and 1.0 <= plan_date < 61.0:
                                    raise except_orm('Lỗi', ("Hãy nhập ngày có thể làm việc >1900 ở dòng: %s") % ([
                                        (rows)]))
                                year, month, day, hour, min, second = xlrd.xldate_as_tuple(plan_date, excel.datemode)
                                plan_date_str = str(year) + "-" + str(month) + "-" + str(day)
                            except:
                                raise except_orm('Lỗi', ("Xem lại ngày có thể làm việc ở dòng: %s") % ([
                                    (rows)]))
                        else:
                            plan_date_str = False
                        work_place = sheet.cell_value(current_row, 11)  #Nơi làm việc
                        applicant_source = sheet.cell_value(current_row, 12) # nguồn ứng viên
                        receiver = sheet.cell_value(current_row, 13) # người nhận hồ sơ

                        applicant_source_id = False
                        receiver_id = False
                        job_id = False
                        job_position_id = False
                        work_place_id = False
                        if work_place:
                            res_country_state = self.env['res.country.state'].search([('code', '=', work_place)])
                            work_place_id = res_country_state.id
                        else:
                            work_place_id = False
                        if applicant_source:
                            hr_applicant_source = self.env['hr.applicant.source'].search([('code', '=', applicant_source)])
                            applicant_source_id = hr_applicant_source.id
                        else:
                            applicant_source_id = False
                        if receiver:
                            hr_employee = self.env['hr.employee'].search(['|', ('x_emp_code_new', '=', str(receiver)), ('x_emp_code', '=', str(receiver))])
                            receiver_id = hr_employee.id
                        else:
                            receiver_id = False
                        if job:
                            hr_job = self.env['hr.job'].search([('code', '=', job)])
                            job_id = hr_job.id
                        else:
                            job_id = False
                        if job_position:
                            hr_job_position = self.env['hr.job.position'].search([('code', '=', job_position)])
                            job_position_id = hr_job_position.id
                        else:
                            job_position_id = False
                        import_file = {
                            'name': name_applicant,
                            'date_of_birth': birthday_str,
                            'gender': gender,
                            'applicant_phone': phone,
                            'current_address': current_address,
                            'applicant_email': email,
                            'account_facebook': account_facebook ,
                            'experience': experience,
                            'job_id': job_id,
                            'job_position_id': job_position_id,
                            'receiver_id': receiver_id,
                            'applicant_source_id': applicant_source_id,
                            'applicant_id': self.id,
                            'plan_date': plan_date_str,
                            'work_place': work_place_id,
                        }

                        upload_file_obj = self.env['import.applicant.detail']
                        upload_file_obj.create(import_file)

        except IndexError as e:

            raise except_orm("Error", str(e))


    def check_format_file_excel(self, file_name):
        if file_name.endswith('.xls') is False and file_name.endswith('.xlsx') is False and file_name.endswith(
                '.xlsb') is False:
            self.file_upload = None
            self.file_name = None
            raise except_orm('Lỗi', "File phải là định dạng 'xlsx' hoặc 'xlsb' hoặc 'xls'")


    @api.multi
    def update_file(self):
        obj_hr_applicant = self.env['hr.applicant']
        for line in self.detail_ids:
            if not line.applicant_phone:
                raise except_orm('Thông báo!', "Phải nhập đầy đủ số điện thoại trước khi tạo mới ứng viên'")
            new_hr_applicant = obj_hr_applicant.create({
                        'partner_name': line.name,
                        'date_of_birth': line.date_of_birth,
                        'gender': line.gender,
                        'applicant_phone': line.applicant_phone,
                        'current_address': line.current_address,
                        'applicant_email': line.applicant_email,
                        'account_facebook': line.account_facebook ,
                        'experience': line.experience,
                        'job_id': line.job_id.id,
                        'job_position_id': line.job_position_id.id,
                        'receiver_id': line.receiver_id.id,
                        'applicant_source_id': line.applicant_source_id.id,
                        'plan_date': line.plan_date,
                        'work_place': line.work_place.id,
                    })
        self.write({'state': 'done'})
        # else:
        #     raise except_orm('Lỗi', 'Chưa có dữ liệu để upload')

    @api.multi
    def dowmload_templates_file_xlsx(self):
        # self.detail_ids.unlink()
        param_obj = self.env['ir.config_parameter']
        base_url = param_obj.get_param('web.base.url')
        url = base_url + '/ev_hr_recruitment/static/description/flie_mau.xlsx'
        return {
            "type": "ir.actions.act_url",
            "url": url,
            "target": "_parent",
        }




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

class import_applicant_detail(models.TransientModel):
    _name = 'import.applicant.detail'

    applicant_id = fields.Many2one('import.applicant')
    name = fields.Char(string='Name')
    date_of_birth = fields.Date(string="Date of birth", required=True)
    gender = fields.Selection(GENDER_SELECTION, default='NU', required=True)
    current_address = fields.Char(string="Current address", required=True)
    work_place = fields.Many2one('res.country.state',string="Work place" )
    experience = fields.Char(string="Experience" )
    applicant_phone = fields.Char(string="applicant phone", required=True)
    applicant_email = fields.Char(string="applicant email")
    account_facebook = fields.Char(string="Account facebook")
    # description_recruited = fields.Text(string="Description recruited")

    job_id = fields.Many2one('hr.job', string="Job")
    applicant_source_id = fields.Many2one('hr.applicant.source', string="Applicant source")
    job_position_id = fields.Many2one('hr.job.position', string="Job position")
    # recent_income = fields.Char(string="Recent income")
    expected_income = fields.Char(string="Expected income")
    plan_date = fields.Date(string="Plan date")
    experience = fields.Selection(selection=[('K', 'No'), ('1_year', '1 year'), ('over_1_year', 'Over 1 year')]
                              , default='') # kinh nghiệm làm việc

    receiver_id = fields.Many2one('hr.employee', string="Receiver") # người nhận hồ sơ


