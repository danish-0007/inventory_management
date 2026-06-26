# -*- coding: utf-8 -*-
from odoo import models, fields, api


class ResPartnerExt(models.Model):
    # Agro fields: village, crops grown, per-customer credit period, field notes, payment ledger
    _inherit = 'res.partner'

    village_id = fields.Many2one('agro.village', string='Village')
    crop_ids = fields.Many2many('agro.crop', string='Crops Grown')
    credit_period = fields.Integer(
        string='Credit Period (Days)',
        default=lambda self: self.env['inventory.config'].get_config().default_credit_period,
        help='Number of days this customer is given to clear a bill before it is marked overdue.'
    )
    note_ids = fields.One2many('agro.customer.note', 'partner_id', string='Notes & Field History')
    payment_ids = fields.One2many('agro.customer.payment', 'partner_id', string='Payments')
    agro_payment_count = fields.Integer(string='Payment Count', compute='_compute_agro_payment_count')
    agro_total_outstanding = fields.Monetary(
        string='Total Outstanding', compute='_compute_agro_total_outstanding',
        currency_field='currency_id'
    )
    risk_classification = fields.Selection([
        ('green', 'Green'),
        ('yellow', 'Yellow'),
        ('red', 'Red'),
    ], string='Risk', compute='_compute_risk_classification', store=True)
    agro_total_purchased = fields.Monetary(
        string='Total Purchased', compute='_compute_agro_total_purchased',
        currency_field='currency_id', store=True
    )

    @api.depends('payment_ids')
    def _compute_agro_payment_count(self):
        for partner in self:
            partner.agro_payment_count = len(partner.payment_ids)

    @api.depends('sale_order_ids.agro_is_overdue', 'sale_order_ids.agro_days_overdue', 'sale_order_ids.agro_is_shop_sale')
    def _compute_risk_classification(self):
        # red = a bill over 60 days late, or 2+ bills currently late; yellow = 1 bill late; else green
        for partner in self:
            overdue = partner.sale_order_ids.filtered(lambda o: o.agro_is_shop_sale and o.agro_is_overdue)
            if any(o.agro_days_overdue > 60 for o in overdue) or len(overdue) >= 2:
                partner.risk_classification = 'red'
            elif overdue:
                partner.risk_classification = 'yellow'
            else:
                partner.risk_classification = 'green'

    @api.depends('sale_order_ids.amount_total', 'sale_order_ids.agro_is_shop_sale')
    def _compute_agro_total_purchased(self):
        for partner in self:
            partner.agro_total_purchased = sum(
                partner.sale_order_ids.filtered('agro_is_shop_sale').mapped('amount_total')
            )

    @api.depends('sale_order_ids.agro_amount_outstanding', 'sale_order_ids.agro_is_shop_sale')
    def _compute_agro_total_outstanding(self):
        for partner in self:
            partner.agro_total_outstanding = sum(
                partner.sale_order_ids.filtered('agro_is_shop_sale').mapped('agro_amount_outstanding')
            )

    def action_view_notes(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Notes & Field History',
            'res_model': 'agro.customer.note',
            'view_mode': 'tree,form',
            'domain': [('partner_id', '=', self.id)],
            'context': {'default_partner_id': self.id},
            'target': 'current',
        }

    def action_view_payments(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Payments',
            'res_model': 'agro.customer.payment',
            'view_mode': 'tree,form',
            'domain': [('partner_id', '=', self.id)],
            'context': {'default_partner_id': self.id},
            'target': 'current',
        }

    def action_receive_payment(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Receive Payment',
            'res_model': 'agro.customer.payment',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_partner_id': self.id},
        }
