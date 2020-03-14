from odoo import models, fields, api, _

class report_training_session(models.TransientModel):
    _name = 'training.report.session'

    session_id = fields.Many2one('training.session', string='Session')


    @api.multi
    def print_report_session(self):
        param_obj = self.pool.get('ir.config_parameter')

        url = param_obj.get_param(self._cr, self._uid, 'birt_url')
        report_name = "baocaodanhsachlop.rptdesign"
        param_str = "&session_id=" + str(self.session_id.id)
        return {
            "type": "ir.actions.act_url",
            "url": url + "" + report_name + param_str,
            "target": "_parent",
        }
