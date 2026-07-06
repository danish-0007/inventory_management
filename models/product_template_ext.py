# -*- coding: utf-8 -*-
from datetime import date, timedelta
from odoo import models, fields, api


class ProductTemplateExt(models.Model):
    # Adds agro fields to Odoo's built-in product — keeps future integrations (website, GST) intact
    _inherit = 'product.template'

    detailed_type = fields.Selection(default='product')
    is_sellable = fields.Boolean(string='Sellable', default=True)        # show in sale wizard
    is_purchasable = fields.Boolean(string='Purchasable', default=True)  # show in purchase wizard
    agro_category_id = fields.Many2one('inventory.category', string='Category')
    agro_company_name = fields.Char(string='Company / Brand')            # manufacturer/supplier brand
    # uom_id (native) used directly — no custom unit field needed
    min_stock = fields.Float(string='Min Stock', default=0.0)            # reorder threshold
    stock_status = fields.Selection([
        ('ok', 'OK'),
        ('low', 'Low'),
        ('out', 'Out of Stock'),
    ], compute='_compute_stock_status', store=True, string='Stock Status')
    default_supplier_id = fields.Many2one('res.partner', string='Default Supplier')
    agro_tax_rate_id = fields.Many2one('agro.tax.rate', string='Tax Rate')

    # Analytics fields — refreshed by nightly cron for dashboard performance
    agro_last_purchase_date = fields.Date(string='Last Purchase Date', compute='_compute_agro_purchase_stats', store=True)
    agro_last_sold_date = fields.Date(string='Last Sold Date', compute='_compute_agro_sold_stats', store=True)
    agro_avg_daily_sales = fields.Float(string='Avg Daily Sales (Qty)', compute='_compute_agro_sold_stats', store=True)
    agro_avg_monthly_sales = fields.Float(string='Avg Monthly Sales (Qty)', compute='_compute_agro_sold_stats', store=True)
    agro_dead_stock_months = fields.Integer(string='Months Without Sales', compute='_compute_agro_sold_stats', store=True)
    agro_reorder_qty = fields.Float(string='Suggested Reorder Qty', compute='_compute_agro_reorder', store=True)

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

    @api.depends('product_variant_ids')
    def _compute_agro_purchase_stats(self):
        # Last purchase date from purchase.order.line for each product
        variant_ids = self.mapped('product_variant_ids').ids
        if variant_ids:
            self.env.cr.execute(
                """
                SELECT pol.product_id, MAX(po.date_order::date)
                FROM purchase_order_line pol
                JOIN purchase_order po ON po.id = pol.order_id
                WHERE pol.product_id = ANY(%s) AND po.state IN ('purchase','done')
                GROUP BY pol.product_id
                """,
                [variant_ids]
            )
            rows = {r[0]: r[1] for r in self.env.cr.fetchall()}
        else:
            rows = {}
        for tmpl in self:
            vid = tmpl.product_variant_ids[:1].id
            tmpl.agro_last_purchase_date = rows.get(vid)

    @api.depends('product_variant_ids')
    def _compute_agro_sold_stats(self):
        # Aggregates sale lines (shop sales only) for last-sold date, avg daily/monthly qty, dead stock age
        today = date.today()
        day30 = today - timedelta(days=30)
        day365 = today - timedelta(days=365)
        variant_ids = self.mapped('product_variant_ids').ids
        if variant_ids:
            self.env.cr.execute(
                """
                SELECT
                    sol.product_id,
                    MAX(so.date_order::date)                              AS last_sold_date,
                    SUM(CASE WHEN so.date_order::date >= %s
                             THEN sol.product_uom_qty ELSE 0 END) / 30.0 AS avg_daily,
                    SUM(CASE WHEN so.date_order::date >= %s
                             THEN sol.product_uom_qty ELSE 0 END) / 12.0 AS avg_monthly
                FROM sale_order_line sol
                JOIN sale_order so ON so.id = sol.order_id
                WHERE sol.product_id = ANY(%s)
                  AND so.agro_is_shop_sale = TRUE
                  AND so.state IN ('sale','done')
                GROUP BY sol.product_id
                """,
                [day30, day365, variant_ids]
            )
            rows = {r[0]: r[1:] for r in self.env.cr.fetchall()}
        else:
            rows = {}
        for tmpl in self:
            vid = tmpl.product_variant_ids[:1].id
            row = rows.get(vid)
            if row:
                last_sold, avg_daily, avg_monthly = row
                tmpl.agro_last_sold_date = last_sold
                tmpl.agro_avg_daily_sales = round(float(avg_daily or 0), 4)
                tmpl.agro_avg_monthly_sales = round(float(avg_monthly or 0), 4)
                if last_sold:
                    tmpl.agro_dead_stock_months = max(0, (today - last_sold).days // 30)
                else:
                    tmpl.agro_dead_stock_months = 999
            else:
                tmpl.agro_last_sold_date = False
                tmpl.agro_avg_daily_sales = 0.0
                tmpl.agro_avg_monthly_sales = 0.0
                tmpl.agro_dead_stock_months = 999  # never sold

    @api.depends('agro_avg_daily_sales', 'min_stock')
    def _compute_agro_reorder(self):
        # Suggested reorder = 30-day buffer — avg_daily × 30, rounded up to nearest whole unit
        # If no sales history, fall back to min_stock as the reorder quantity
        import math
        for p in self:
            if p.agro_avg_daily_sales > 0:
                p.agro_reorder_qty = math.ceil(p.agro_avg_daily_sales * 30)
            elif p.min_stock > 0:
                p.agro_reorder_qty = p.min_stock
            else:
                p.agro_reorder_qty = 0.0
