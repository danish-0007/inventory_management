# -*- coding: utf-8 -*-
from datetime import timedelta
from odoo import models, fields, api


class SaleOrderExt(models.Model):
    # Adds payment method, shop-sale flag, and a lightweight credit ledger to Odoo's standard sale order
    _inherit = 'sale.order'

    agro_payment_method = fields.Selection([
        ('cash', 'Cash'),
        ('upi', 'UPI'),
        ('bank_transfer', 'Bank Transfer'),
        ('credit', 'Credit'),
        ('other', 'Other'),
    ], string='Payment Method', default='cash')
    # Used to filter Sales History so only shop sales show (not other Odoo orders)
    agro_is_shop_sale = fields.Boolean(string='Shop Sale', default=False)

    agro_amount_paid = fields.Monetary(string='Amount Paid', currency_field='currency_id')
    agro_amount_outstanding = fields.Monetary(
        string='Amount Outstanding', compute='_compute_agro_amount_outstanding',
        store=True, currency_field='currency_id'
    )
    agro_due_date = fields.Date(string='Due Date', compute='_compute_agro_due_date', store=True)
    agro_is_overdue = fields.Boolean(string='Overdue', compute='_compute_agro_overdue', store=True)
    agro_days_overdue = fields.Integer(string='Days Overdue', compute='_compute_agro_overdue', store=True)
    agro_products_summary = fields.Char(
        string='Products', compute='_compute_agro_products_summary', store=True
    )
    agro_total_profit = fields.Monetary(
        string='Total Profit', compute='_compute_agro_profit_totals',
        store=True, currency_field='currency_id'
    )
    agro_cost_total = fields.Monetary(
        string='Cost Total', compute='_compute_agro_profit_totals',
        store=True, currency_field='currency_id'
    )

    @api.depends('amount_total', 'agro_amount_paid')
    def _compute_agro_amount_outstanding(self):
        for order in self:
            order.agro_amount_outstanding = order.amount_total - order.agro_amount_paid

    @api.depends('date_order', 'partner_id.credit_period')
    def _compute_agro_due_date(self):
        for order in self:
            order_date = order.date_order.date() if order.date_order else fields.Date.context_today(order)
            order.agro_due_date = order_date + timedelta(days=order.partner_id.credit_period or 0)

    @api.depends('agro_due_date', 'agro_amount_outstanding')
    def _compute_agro_overdue(self):
        today = fields.Date.context_today(self)
        for order in self:
            if order.agro_due_date and order.agro_amount_outstanding > 0.005 and order.agro_due_date < today:
                order.agro_is_overdue = True
                order.agro_days_overdue = (today - order.agro_due_date).days
            else:
                order.agro_is_overdue = False
                order.agro_days_overdue = 0

    @api.depends('order_line.product_id')
    def _compute_agro_products_summary(self):
        for order in self:
            order.agro_products_summary = ', '.join(order.order_line.mapped('product_id.name'))

    @api.depends('order_line.agro_profit', 'order_line.agro_cost')
    def _compute_agro_profit_totals(self):
        for order in self:
            order.agro_total_profit = sum(order.order_line.mapped('agro_profit'))
            order.agro_cost_total = sum(order.order_line.mapped('agro_cost'))

    def action_confirm(self):
        # Odoo's own action_confirm() always resets date_order to now() (_prepare_confirmation_values) —
        # restore the operator's chosen date for shop sales right after, so backdated entries stick.
        # Cash/UPI/other are settled at the counter immediately — only "Credit" carries a balance.
        chosen_dates = {order.id: order.date_order for order in self if order.agro_is_shop_sale}
        res = super().action_confirm()
        for order in self:
            if order.agro_is_shop_sale:
                if chosen_dates.get(order.id):
                    order.date_order = chosen_dates[order.id]
                if order.agro_payment_method != 'credit':
                    order.agro_amount_paid = order.amount_total
        return res

    @api.model
    def _cron_update_overdue_status(self):
        # agro_is_overdue/agro_days_overdue depend on "today", which doesn't fire @api.depends on
        # its own — this nightly job force-recomputes them so yesterday's not-yet-due bill that
        # crossed its due date overnight gets flagged (and partner risk_classification cascades).
        open_orders = self.search([
            ('agro_is_shop_sale', '=', True),
            ('agro_amount_outstanding', '>', 0.005),
        ])
        open_orders._compute_agro_overdue()


class SaleOrderLineExt(models.Model):
    # Stores the batch sold per line — for receipt printing, profit computation, and history traceability
    _inherit = 'sale.order.line'

    agro_lot_id = fields.Many2one('stock.lot', string='Batch')
    agro_sold_qty = fields.Float(string='Sold Qty')
    agro_sold_uom_id = fields.Many2one('uom.uom', string='Sold Unit')
    agro_profit = fields.Monetary(
        string='Line Profit', compute='_compute_agro_profit',
        store=True, currency_field='currency_id'
    )
    agro_cost = fields.Monetary(
        string='Line Cost', compute='_compute_agro_profit',
        store=True, currency_field='currency_id'
    )

    @api.depends('product_uom_qty', 'price_unit', 'discount', 'agro_lot_id', 'agro_lot_id.unit_price')
    def _compute_agro_profit(self):
        # Profit = (sell_price_after_discount - lot_cost_price) × qty_in_base_uom
        # cost defaults to 0 when lot has no recorded purchase cost (profit = full revenue)
        for line in self:
            qty = line.product_uom_qty
            sell_price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
            cost_price = line.agro_lot_id.unit_price if line.agro_lot_id else 0.0
            line.agro_cost = cost_price * qty
            line.agro_profit = (sell_price - cost_price) * qty
