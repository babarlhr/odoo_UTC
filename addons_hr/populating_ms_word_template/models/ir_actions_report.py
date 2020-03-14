# -*- coding: utf-8 -*-
from addons_hr.populating_ms_word_template.models.mailmerge import MailMerge
from odoo import models, fields, api
from odoo.exceptions import UserError, AccessError
import mailmerge
from lxml import etree
import binascii
import tempfile
import base64
from zipfile import ZipFile, ZIP_DEFLATED
from io import BytesIO
from odoo.tools.safe_eval import safe_eval
from datetime import datetime,date
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, pycompat, float_repr
from dateutil.relativedelta import relativedelta




class IrActionsReport(models.Model):
    _inherit = 'ir.actions.report'

    report_type = fields.Selection([
        ('qweb-html', 'HTML'),
        ('qweb-pdf', 'PDF'),
        ('qweb-text', 'Text'),
        ('doc','MS Word'),
        # ('excel', 'Ms Excel'),
    ], required=True, default='qweb-pdf',
        help='The type of the report that will be rendered, each one having its own'
             ' rendering method. HTML means the report will be opened directly in your'
             ' browser PDF means the report will be rendered using Wkhtmltopdf and'
             ' downloaded by the user.')


    file_template_data = fields.Binary('File template', attachment=True)
    file_template_name = fields.Char('File template')

    def _convert_binary_to_doc(self, file_template_data=None, suffix='.docx'):
        fp = tempfile.NamedTemporaryFile(suffix=suffix)
        if file_template_data == None:
            fp.write(binascii.a2b_base64(self.file_template_data))
        else:
            fp.write(binascii.a2b_base64(file_template_data))
        fp.seek(0)
        return fp

    def _get_file_format(self, file_name):
        return str(file_name).split(".")[-1]

    def format_numbers(number):
        # format number to str with between 2 and 8 decimals (event if it's .00)
        number_splited = str(number).split('.')
        if len(number_splited) == 1:
            return "%.02f" % number

        cents = number_splited[1]
        if len(cents) > 8:
            return "%.08f" % number
        return float_repr(number, max(2, len(cents)))

    @api.multi
    def export_doc_by_template(self, file_template_data=None, suffix='docx', file_name_export='export1', datas={}):
        simple_merge = {}
        populating_tables = {}
        file_template = self._convert_binary_to_doc(file_template_data=file_template_data,suffix=suffix)
        document = MailMerge(file_template.name)
        fields = document.get_merge_fields()
        for field in fields:
            childs = field.split('.')
            if len(childs) == 1:
                value = getattr(datas, childs[0], '')
                if isinstance(value, datetime):
                    value = (value + relativedelta(hours=7)).strftime(
                        self.env['res.lang'].search([('code', '=', self.env.user.lang)], limit=1).date_format + ' ' +
                        self.env['res.lang'].search([('code', '=', self.env.user.lang)], limit=1).time_format)
                elif isinstance(value, date):
                    value = value.strftime(self.env['res.lang'].search([('code', '=', self.env.user.lang)], limit=1).date_format)
                elif isinstance(value, (float, int)):
                    value = '{:,.2f}'.format(value).replace(',', ' ')
                else:
                    value = str(value)
                if value == False:
                    value = ''
                simple_merge[field] = value
            else:
                childs[0] = childs[0].replace('»','').replace('«','')
                if childs[0] == 'line':
                    childs.remove(childs[0])
                    key = childs[0]
                    data_array = getattr(datas, key)
                    childs.remove(key)
                    tmp_val = []
                    value_field = {}
                    for data in data_array:
                        for child in childs:
                            data = getattr(data, child)
                        if isinstance(data, datetime):
                            data = (data + relativedelta(hours=7)).strftime(
                                self.env['res.lang'].search([('code', '=', self.env.user.lang)], limit=1).date_format + ' ' + self.env['res.lang'].search([('code', '=', self.env.user.lang)], limit=1).time_format)
                        elif isinstance(data, date):
                            data = data.strftime(
                                self.env['res.lang'].search([('code', '=', self.env.user.lang)], limit=1).date_format)
                        elif isinstance(data, (float, int)):
                            data = '{:,.2f}'.format(data).replace(',', ' ')
                        else:
                            data = str(data)
                        if data == False:
                            data = ''
                        tmp_val.append(data)

                    value_field[field] = tmp_val
                    if key in populating_tables:
                        populating_tables[key].append(value_field)
                    else:
                        tmp_value = []
                        tmp_value.append(value_field)
                        populating_tables[key] = tmp_value
                else:
                    if len(childs) <= 0:
                        simple_merge[field] = ''
                        continue
                    tmp_logic = childs[len(childs)-1].replace('«','').replace('»', '')
                    if tmp_logic == 'sum':
                        data_array = getattr(datas, childs[0].replace('«','').replace('»', ''))
                        sum = 0
                        for data in data_array:
                            childs[1] = childs[1].replace('»', '').replace('«', '')
                            value = getattr(data, childs[1])
                            sum += value
                        if isinstance(sum, (float, int)):
                            sum = '{:,.2f}'.format(sum).replace(',', ' ')
                        simple_merge[field] = str(sum)
                    elif tmp_logic == 'count':
                        childs[0] = childs[0].replace('»', '').replace('«', '')
                        data_array = getattr(datas, childs[0])
                        count = len(data_array)
                        if isinstance(count, (float, int)):
                            count = '{:,.2f}'.format(count).replace(',', ' ')
                        simple_merge[field] = str(count)
                    else:
                        data = datas
                        for child in childs:
                            child = child.replace('«','').replace('»','')
                            data = getattr(data,child)
                        if isinstance(data, datetime):
                            data = (data + relativedelta(hours=7)).strftime(
                                self.env['res.lang'].search([('code', '=', self.env.user.lang)],
                                                            limit=1).date_format + ' ' + self.env[
                                    'res.lang'].search([('code', '=', self.env.user.lang)], limit=1).time_format)
                        elif isinstance(data, date):
                            data = data.strftime(
                                self.env['res.lang'].search([('code', '=', self.env.user.lang)],
                                                            limit=1).date_format)
                        elif isinstance(data, (float, int)):
                            data = '{:,.2f}'.format(data).replace(',', ' ')
                        else:
                            data = str(data)
                        if data == False:
                            data = ''
                        simple_merge[field] = str(data)
        for key in simple_merge:
            if simple_merge[key] == False:
                simple_merge[key] = ''
        document.merge(**simple_merge)
        for key in populating_tables:
            value = populating_tables[key]
            list = []
            anchor = ''
            number = 0
            if number == 0:
                for k in value[0]:
                    val = value[0][k]
                    number = len(val)
                    break
            for i in range(number):
                dict = {}
                for val in value:
                    for k in val:
                        v = val[k]
                        dict[k] = v[i]
                        if anchor == '':
                            anchor = k
                        break
                list.append(dict)
            document.merge_rows(anchor, list)

        for field in document.get_merge_fields():
            document.merge(**{field: ''})

        mem_zip = BytesIO()
        with ZipFile(mem_zip, 'w', ZIP_DEFLATED) as output:
            for zi in document.zip.filelist:
                if zi in document.parts:
                    xml = etree.tostring(document.parts[zi].getroot())
                    output.writestr(zi.filename, xml)
                elif zi == document._settings_info:
                    xml = etree.tostring(document.settings.getroot())
                    output.writestr(zi.filename, xml)
                else:
                    output.writestr(zi.filename, document.zip.read(zi))

        file_data = mem_zip.getvalue()
        vals = {
            'name': safe_eval(file_name_export, {'object': datas}) + '.' + suffix,
            'datas': base64.b64encode(file_data),
            'datas_fname': safe_eval(file_name_export, {'object': datas}) + '.' + suffix,
            'type': 'binary',
            'res_model': self.model,
            'res_id': datas.id,
        }
        file_id = self.env['ir.attachment'].create(vals)
        return {
            'type': 'ir.actions.act_url',
            'url': '/web/content/' + str(file_id.id) + '?download=true',
            'target': 'new'
        }

    def _get_suffix(self):
        return str(self.file_template_name).split(".")[-1]

    @api.noguess
    def report_action(self, docids, data=None, config=True):
        if self.report_type != 'doc':
            return super(IrActionsReport, self).report_action(docids,data,config)
        suffix = self._get_suffix()
        return self.export_doc_by_template(datas=docids, file_name_export=self.print_report_name,suffix=suffix)

