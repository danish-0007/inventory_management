# -*- coding: utf-8 -*-
from odoo import models, fields


class AgroCrop(models.Model):
    # Master list of crops — links customers and sale lines for crop-wise purchase history
    _name = 'agro.crop'
    _description = 'Crop'
    _order = 'name'

    name = fields.Char(string='Crop', required=True)
    active = fields.Boolean(default=True)
