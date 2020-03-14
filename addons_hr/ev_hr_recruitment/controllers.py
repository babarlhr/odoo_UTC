# -*- coding: utf-8 -*-
import openerp.addons.web.controllers.main as base_main
import logging
from openerp import http, _, api
import json
import xmlrpclib

_logger = logging.getLogger(__name__)

CODE_PARAM_NOT_PROVIDED = 1001
CODE_PARAM_INVALID = 1002
CODE_SYSTEM_ERROR = 1003

class EvHrRecruitment(base_main.DataSet):
    def do_search_read(self, model, fields=False, offset=0, limit=False, domain=None, sort=None, context=None):
        if model == 'hr.recruitment.request':
            if domain is None:
                domain = []
            ctx = dict(http.request.context or {})
            user_obj = http.request.env['res.users']
            ctx = http.request.context
            view_id = ctx.get('view', False)
            is_sale_manager = user_obj.has_group('base.group_sale_manager')
            is_sale_salesman_all_leads = user_obj.has_group('base.group_sale_salesman_all_leads')
            is_hr_manager = user_obj.has_group('base.group_hr_manager')
            is_hr_user = user_obj.has_group('base.group_hr_user')
            print("is_sale_manager: " + str(is_sale_manager))
            print("is_sale_salesman_all_leads: " + str(is_sale_salesman_all_leads))
            print("is_hr_manager: " + str(is_hr_manager))
            print("is_hr_user: " + str(is_hr_user))
            if not (http.request.env.uid == 1):
                if is_hr_manager or is_hr_user:
                    domain += [['state', '!=', 'draft']]
                elif is_sale_manager or is_sale_salesman_all_leads:
                    domain += [['create_uid', '=', http.request.env.user.id]]
                else:
                    domain += [['create_uid', '=', http.request.env.user.id]]
        return super(EvHrRecruitment, self).do_search_read(model, fields, offset, limit, domain, sort)


class ApiException(Exception):
    def __init__(self, message, code=0):
        self.message = message
        self.code = code

class ApiController(http.Controller):
    @http.route(route='/ev_hr_recruitment/convert_base64_attachment', type='json', auth='public', methods=['POST'], website=True)
    def convert_base64_attachment(self, **kwargs):
        try:
            # response_obj = self.do_get_response_callback()
            # return http.Response(json.dumps(response_obj))
            #ids = '19392,24348,24389,24364,25206,14293,24344,19590,24892,24372'

            params = http.request.jsonrequest
            cr = http.request.cr
            env = api.Environment(cr, 1, {})
            obj_partner_rank_history = env['partner.rank.history']
            obj_ir_attachment = env['ir.attachment']
            obj_hr_applicant = env['hr.applicant']

            # partner_rank_histories = obj_partner_rank_history.search(['|', ('form_img_attachment_id', '=', False),
            #                                                           ('signature_img_attachment_id', '=', False)], limit=100)
            # query = """ SELECT id FROM partner_rank_history WHERE form_img_attachment_id is null or signature_img_attachment_id is null LIMIT 1000 """
            # cr.execute(query, ())
            # res = cr.dictfetchall()
            # if res:
            #     for r in res:
            #         partner_rank_his = obj_partner_rank_history.search([('id', '=', r['id'])])
            #         if partner_rank_his.form_img and not  partner_rank_his.form_img_attachment_id:
            #             attachment_id = obj_ir_attachment.create({'name': 'demo', 'datas': partner_rank_his.form_img})
            #             print("ngadv: " +str(attachment_id))
            #             partner_rank_his.write({
            #                 'form_img_attachment_id': attachment_id.id,
            #             })
            #             cr.commit()
            #         if partner_rank_his.signature_img and not partner_rank_his.signature_img_attachment_id:
            #             signature_attachment_id = obj_ir_attachment.create({'name': 'demo', 'datas': partner_rank_his.signature_img})
            #             print("ngadv1: " +str(signature_attachment_id))
            #             partner_rank_his.write({
            #                 'signature_img_attachment_id': signature_attachment_id.id,
            #             })
            #             cr.commit()

            # applicants = obj_hr_applicant.search(['id', '=', 0])
            query_applicant = """ SELECT id FROM hr_applicant WHERE avatar_attachment_id is null LIMIT 1000 """
            cr.execute(query_applicant, ())
            res_applicant = cr.dictfetchall()
            for r in res_applicant:
                applicant = obj_hr_applicant.search([('id', '=', r['id'])])
                if applicant.avatar and not applicant.avatar_attachment_id:
                    attachment_id = obj_ir_attachment.create({'name': 'demo', 'datas': applicant.avatar})
                    print("ngadv: " +str(attachment_id))
                    applicant.write({
                        'avatar_attachment_id': attachment_id.id,
                    })
                    cr.commit()

            print('context:' + str(http.request.context))
            return {'name': 'ngadv'}
        except xmlrpclib.Fault as e:
            response_object = {'code': CODE_SYSTEM_ERROR, 'message': e.faultString}
            return http.Response(json.dumps(response_object))
        # except ApiException, e:
        #     response_object = {'code': e.code, 'message': e.message}
        #     return http.Response(json.dumps(response_object))
