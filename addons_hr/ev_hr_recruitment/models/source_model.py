__author__ = 'HienTN'
from odoo import fields, models, api


class SourceModel(models.Model):
    _name = 'hr.applicant.source'

    name = fields.Char(string='Name', required=True)
    code = fields.Char(string="Code", required=True)
