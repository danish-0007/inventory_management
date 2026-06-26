# -*- coding: utf-8 -*-
from odoo import models, fields


class AgroVillage(models.Model):
    # Master list of villages — used to group customers for the Village Report
    _name = 'agro.village'
    _description = 'Village'
    _order = 'name'

    name = fields.Char(string='Village', required=True)
    active = fields.Boolean(default=True)
