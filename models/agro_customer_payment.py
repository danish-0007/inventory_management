# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class AgroCustomerPayment(models.Model):
    # Money received from a customer — auto-applied to their oldest unpaid bills first (FIFO)
    _name = 'agro.customer.payment'
    _description = 'Customer Payment'
    _order = 'payment_date desc, id desc'

    partner_id = fields.Many2one('res.partner', string='Customer', required=True, index=True, ondelete='cascade')
    payment_date = fields.Date(string='Date', default=fields.Date.context_today, required=True)
    amount = fields.Monetary(string='Amount Received', required=True, currency_field='currency_id')
    currency_id = fields.Many2one(
        'res.currency', string='Currency', default=lambda self: self.env.company.currency_id
    )
    payment_method = fields.Selection([
        ('cash', 'Cash'),
        ('upi', 'UPI'),
        ('other', 'Other'),
    ], string='Method', default='cash', required=True)
    note = fields.Char(string='Note')
    user_id = fields.Many2one('res.users', string='Received By', default=lambda self: self.env.user)
    allocation_ids = fields.One2many('agro.customer.payment.allocation', 'payment_id', string='Applied To')

    @api.model_create_multi
    def create(self, vals_list):
        payments = super().create(vals_list)
        payments._allocate_fifo()
        return payments

    def write(self, vals):
        if ('amount' in vals or 'partner_id' in vals) and any(p.allocation_ids for p in self):
            raise UserError(_(
                'This payment has already been applied to bills. '
                'Delete it and record a new payment instead of changing the amount or customer.'
            ))
        return super().write(vals)

    def unlink(self):
        for payment in self:
            for allocation in payment.allocation_ids:
                allocation.sale_order_id.agro_amount_paid -= allocation.amount_allocated
        return super().unlink()

    def _allocate_fifo(self):
        # Applies each payment to the customer's oldest unpaid bill first, spilling into the next
        for payment in self:
            remaining = payment.amount
            orders = self.env['sale.order'].search([
                ('partner_id', '=', payment.partner_id.id),
                ('agro_is_shop_sale', '=', True),
                ('agro_amount_outstanding', '>', 0.005),
            ], order='date_order asc')
            for order in orders:
                if remaining <= 0.005:
                    break
                applied = min(remaining, order.agro_amount_outstanding)
                self.env['agro.customer.payment.allocation'].create({
                    'payment_id': payment.id,
                    'sale_order_id': order.id,
                    'amount_allocated': applied,
                })
                order.agro_amount_paid += applied
                remaining -= applied


class AgroCustomerPaymentAllocation(models.Model):
    # One slice of a payment applied to a specific bill — the audit trail behind the FIFO split
    _name = 'agro.customer.payment.allocation'
    _description = 'Customer Payment Allocation'

    payment_id = fields.Many2one('agro.customer.payment', required=True, ondelete='cascade')
    sale_order_id = fields.Many2one('sale.order', string='Bill', required=True, ondelete='cascade')
    amount_allocated = fields.Monetary(string='Amount Applied', currency_field='currency_id')
    currency_id = fields.Many2one(related='payment_id.currency_id', string='Currency')
