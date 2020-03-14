from odoo import models, fields, api, _

class training_major(models.Model):
    _name = 'training.major'

    name = fields.Char(String='Name')
    major_code = fields.Char(string=_('Code'), help=_('The code will be generated automatically'), select=True,
                             default='/', readonly=False, required=True)
    description = fields.Text(String='Description')

    @api.model
    def create(self, vals):
        if 'major_code' not in vals or vals['major_code'] == _('New'):
            vals['major_code'] = self.env['ir.sequence'].next_by_code('training_major_name_seq') or _('New')
        return super(training_major, self).create(vals)


