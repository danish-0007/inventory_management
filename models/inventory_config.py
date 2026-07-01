# -*- coding: utf-8 -*-
from odoo import models, fields, api


class InventoryConfig(models.Model):
    # Singleton config — shop name, logo, GST, receipt footer, expiry warning threshold
    _name = 'inventory.config'
    _description = 'Agro Shop Configuration'

    name = fields.Char(default='Shop Configuration')
    shop_name = fields.Char(string='Shop Name', required=True, default='Agro & Seeds Shop')
    shop_address = fields.Text(string='Address')
    shop_phone = fields.Char(string='Phone')
    shop_logo = fields.Binary(string='Logo')
    gst_number = fields.Char(string='GST Number')
    receipt_footer = fields.Text(string='Receipt Footer Message')
    expiry_warning_days = fields.Integer(string='Expiry Warning (days)', default=30)
    default_credit_period = fields.Integer(string='Default Credit Period (days)', default=30)
    # Auto-filled as customer on every new sale — no need to pick a customer for cash sales
    default_walkin_partner_id = fields.Many2one(
        'res.partner', string='Walk-in Customer',
        help='Default customer used for walk-in sales'
    )
    @api.model
    def get_config(self):
        # Always use this instead of search() — creates a default if none exists
        config = self.search([], limit=1)
        if not config:
            config = self.create({'shop_name': 'Agro & Seeds Shop'})
        return config
