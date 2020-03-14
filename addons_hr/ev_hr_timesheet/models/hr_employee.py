# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
import logging
import time
from dateutil.relativedelta import relativedelta
from datetime import datetime
import random

_logger = logging.getLogger(__name__)


class hr_timesheet_employee(models.Model):
    _inherit = 'hr.employee'

    default_shift_id = fields.Many2one('hr.employee.shift', string='Shift')


