# -*- coding: utf-8 -*-
from odoo import models, fields, api


class StockLotExt(models.Model):
    # Adds expiry tracking and purchase info to Odoo's built-in batch/lot model
    _inherit = 'stock.lot'

    purchase_date = fields.Date(string='Purchase Date')
    unit_price = fields.Float(string='Cost Price')
    auto_batch_sequence = fields.Boolean(string='Auto Generated', default=False)
    days_to_expiry = fields.Integer(compute='_compute_expiry_info', string='Days to Expiry', store=True)
    expiry_status = fields.Selection([
        ('ok', 'OK'),
        ('expiring', 'Expiring Soon'),
        ('expired', 'Expired'),
    ], compute='_compute_expiry_info', store=True, string='Expiry Status')

    @api.depends('expiration_date')
    def _compute_expiry_info(self):
        # Computes days left and status; warning threshold comes from shop config
        today = fields.Date.today()
        config = self.env['inventory.config'].search([], limit=1)
        warning_days = config.expiry_warning_days if config else 30
        for lot in self:
            if not lot.expiration_date:
                lot.days_to_expiry = 0
                lot.expiry_status = 'ok'
                continue
            delta = (lot.expiration_date - today).days
            lot.days_to_expiry = delta
            if delta < 0:
                lot.expiry_status = 'expired'
            elif delta <= warning_days:
                lot.expiry_status = 'expiring'
            else:
                lot.expiry_status = 'ok'

    @api.model_create_multi
    def create(self, vals_list):
        # Auto-generates batch name from sequence if none is provided
        for vals in vals_list:
            if not vals.get('name'):
                vals['name'] = self.env['ir.sequence'].next_by_code('agro.batch') or '/'
                vals['auto_batch_sequence'] = True
        return super().create(vals_list)
