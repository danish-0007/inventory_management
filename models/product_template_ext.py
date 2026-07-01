# -*- coding: utf-8 -*-
from odoo import models, fields, api


class ProductTemplateExt(models.Model):
    # Adds agro fields to Odoo's built-in product — keeps future integrations (website, GST) intact
    _inherit = 'product.template'

    detailed_type = fields.Selection(default='product')
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
    agro_tax_rate_id = fields.Many2one('agro.tax.rate', string='Tax Rate')

    # No @api.depends — always live-computed so count stays fresh after goods receipts
    lot_count = fields.Integer(compute='_compute_lot_count', string='Batches')

    @api.depends()
    def _compute_lot_count(self):
        all_variant_ids = self.mapped('product_variant_ids').ids
        if all_variant_ids:
            lot_data = self.env['stock.lot'].read_group(
                [('product_id', 'in', all_variant_ids), ('product_qty', '>', 0)],
                ['product_id'],
                ['product_id'],
            )
            count_map = {d['product_id'][0]: d['product_id_count'] for d in lot_data}
        else:
            count_map = {}
        for tmpl in self:
            tmpl.lot_count = sum(count_map.get(vid, 0) for vid in tmpl.product_variant_ids.ids)

    def action_view_lot_ids(self):
        self.ensure_one()
        action = self.env['ir.actions.act_window']._for_xml_id('inventory_management.action_agro_batches')
        action['domain'] = [('product_id', 'in', self.product_variant_ids.ids)]
        return action

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
