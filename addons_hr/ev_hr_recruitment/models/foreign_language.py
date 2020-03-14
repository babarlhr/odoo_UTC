__author__ = 'dovietnga0909'

from odoo import models, fields, api

class foreign_language(models.Model):
    _name = 'hr.foreign.language'

    foreign_language = fields.Char(string="Foreign language")
    listen_skill = fields.Char(string="Listen skill")
    speak_skill = fields.Char(string="Speak skill")
    read_skill = fields.Char(string="Read skill")
    write_skill = fields.Char(string="Write skill")

    applicant_id = fields.Many2one('hr.applicant', string="Applicant", ondelete='cascade', required=True)

