# -*- coding: utf-8 -*-
import logging
from lxml import etree

from odoo import models, fields, api, _
from datetime import datetime
from dateutil.relativedelta import relativedelta
from odoo.exceptions import except_orm, ValidationError
from dateutil.relativedelta import relativedelta
import base64
import xlrd

_logger = logging.getLogger(__name__)


class account_period(models.Model):
    _name = "account.period"
    _description = "Account period"


    name=fields.Char('Period Name', required=True)
    code = fields.Char('Code', size=12)
    date_start = fields.Date('Start of Period', required=True)
    date_stop = fields.Date('End of Period', required=True)

