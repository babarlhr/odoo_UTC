# -*- coding: utf-8 -*-
from openerp import http

# class EvEducationCourse(http.Controller):
#     @http.route('/ev_education_course/ev_education_course/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/ev_education_course/ev_education_course/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('ev_education_course.listing', {
#             'root': '/ev_education_course/ev_education_course',
#             'objects': http.request.env['ev_education_course.ev_education_course'].search([]),
#         })

#     @http.route('/ev_education_course/ev_education_course/objects/<model("ev_education_course.ev_education_course"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('ev_education_course.object', {
#             'object': obj
#         })