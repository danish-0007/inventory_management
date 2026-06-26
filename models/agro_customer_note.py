# -*- coding: utf-8 -*-
from odoo import models, fields


class AgroCustomerNote(models.Model):
    # Field history / observations logged against a customer — newest first
    _name = 'agro.customer.note'
    _description = 'Customer Note'
    _order = 'note_date desc'

    partner_id = fields.Many2one('res.partner', string='Customer', required=True, index=True, ondelete='cascade')
    note_date = fields.Datetime(string='Date', default=fields.Datetime.now, required=True)
    user_id = fields.Many2one('res.users', string='Added By', default=lambda self: self.env.user, required=True)
    description = fields.Text(string='Note', required=True)
