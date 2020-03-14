# -*- coding: utf-8 -*-
from odoo import fields, models, api

class applicant_status(models.Model):
    _name = 'hr.applicant.status'

    name = fields.Char(string='Name', required=True)
    code = fields.Char(string='Code', required=True)

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        print("applicant_status.py > def name_search")
        context = self._context
        print("applicant_status.py self._context: " + str(self._context))
        cr = self._cr
        query = ''' select a.id, a.name, a.code from hr_applicant_status a '''
        cr.execute(query, )
        status = cr.dictfetchall()
        result = []
        for s in status:
            result.append([s['id'], '[' + s['code'] + '] - ' + s['name']])
        res = result
        return res

    def name_get(self, cr, uid, ids, context=None):
        res = []
        for a in self.browse(cr, uid, ids, context=context):
            res.append([a.id, '[' + a.code + '] - ' + a.name])
        return res
