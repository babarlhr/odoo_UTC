__author__ = 'dovietnga0909'
from odoo import fields, models, api

class family_relationship(models.Model):
    _name = 'hr.family.relationship'

    full_name = fields.Char(string="Full name")
    relationship = fields.Char(string="Relationship")
    year_of_birth = fields.Char(string="Year of birth")
    job = fields.Char(string="Job")
    work_unit = fields.Char(string="Work unit")

    applicant_id = fields.Many2one('hr.applicant', string="Applicant", ondelete='cascade', required=True)
