# -*- coding: utf-8 -*-
import base64
import datetime
from datetime import timedelta
import xlrd
from dateutil.relativedelta import relativedelta
from odoo import models, fields, api
from odoo.exceptions import except_orm
import logging

_logger = logging.getLogger(__name__)

class ImportTemplate(models.TransientModel):
    _name = 'import.template'

    file_upload = fields.Binary(string='File upload')
    file_name = fields.Char(string='File name')

    def check_format_file_excel(self, file_name):
        if file_name.endswith('.xls') is False and file_name.endswith('.xlsx') is False and file_name.endswith('.xlsb') is False:
            self.file_upload = None
            self.file_name = None
            raise except_orm('Lỗi', "File phải là định dạng 'xlsx' hoặc 'xlsb' hoặc 'xls'")

    def import_employee(self):
        if not self.file_upload:
            raise except_orm('Thông báo', 'Bạn cần chọn file trước')
        """ Kiểm tra định dạng file """
        self.check_format_file_excel(self.file_name)
        data = self.file_upload
        data_file = base64.decodebytes(data)
        excel = xlrd.open_workbook(file_contents=data_file)
        sheet = excel.sheet_by_index(0)
        # if sheet.nrows > 1002:
        #     raise except_orm('Thông báo', 'Để đảm bảo cập nhật thành công, hãy cập nhật dưới 1000 dòng')
        str_partner_created = ''
        for rows in range(sheet.nrows):
            current_row = rows
            x_emp_code = str(sheet.cell_value(current_row, 0)).strip()
            name = str(sheet.cell_value(current_row, 1)).strip()
            hr_emp = self.env['hr.employee'].search([('name', '=', 'name')], limit=1)
            if hr_emp:
                hr_emp.write({
                    'x_emp_code': x_emp_code,
                    'x_emp_code_new': x_emp_code,
                })
