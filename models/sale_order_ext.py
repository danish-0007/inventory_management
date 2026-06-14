# -*- coding: utf-8 -*-
from odoo import models, fields


class SaleOrderExt(models.Model):
    # Adds payment method and shop-sale flag to Odoo's standard sale order
    _inherit = 'sale.order'

    agro_payment_method = fields.Selection([
        ('cash', 'Cash'),
        ('upi', 'UPI'),
        ('credit', 'Credit'),
        ('other', 'Other'),
    ], string='Payment Method', default='cash')
    # Used to filter Sales History so only shop sales show (not other Odoo orders)
    agro_is_shop_sale = fields.Boolean(string='Shop Sale', default=False)


class SaleOrderLineExt(models.Model):
    # Stores the batch sold per line — for receipt printing and history traceability
    _inherit = 'sale.order.line'

    agro_lot_id = fields.Many2one('stock.lot', string='Batch')
    agro_sold_qty = fields.Float(string='Sold Qty')
    agro_sold_uom_id = fields.Many2one('uom.uom', string='Sold Unit')
