# -*- coding: utf-8 -*-
from odoo import models, fields, api


class ProductTemplateExt(models.Model):
    # Adds agro fields to Odoo's built-in product — keeps future integrations (website, GST) intact
    _inherit = 'product.template'

    is_sellable = fields.Boolean(string='Sellable', default=True)        # show in sale wizard
    is_purchasable = fields.Boolean(string='Purchasable', default=True)  # show in purchase wizard
    agro_category_id = fields.Many2one('inventory.category', string='Category')
    # uom_id (native) used directly — no custom unit field needed
    min_stock = fields.Float(string='Min Stock', default=0.0)            # reorder threshold
    stock_status = fields.Selection([
        ('ok', 'OK'),
        ('low', 'Low'),
        ('out', 'Out of Stock'),
    ], compute='_compute_stock_status', store=True, string='Stock Status')
    default_supplier_id = fields.Many2one('res.partner', string='Default Supplier')

    @api.depends('qty_available', 'min_stock')
    def _compute_stock_status(self):
        # ok = above min, low = at or below min, out = zero stock
        # if min_stock is 0 (not set), 'low' never triggers — only ok/out
        for p in self:
            if p.qty_available <= 0:
                p.stock_status = 'out'
            elif p.min_stock > 0 and p.qty_available <= p.min_stock:
                p.stock_status = 'low'
            else:
                p.stock_status = 'ok'
