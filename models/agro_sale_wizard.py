# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import UserError


class AgroSaleWizard(models.TransientModel):
    # Temporary sale form — creates a real sale.order on confirm, then opens receipt PDF
    _name = 'agro.sale.wizard'
    _description = 'New Sale'

    customer_id = fields.Many2one('res.partner', string='Customer', required=True)
    date = fields.Date(string='Date', default=fields.Date.today)
    payment_method = fields.Selection([
        ('cash', 'Cash'),
        ('upi', 'UPI'),
        ('credit', 'Credit'),
        ('other', 'Other'),
    ], string='Payment Method', default='cash', required=True)
    notes = fields.Text(string='Notes')
    line_ids = fields.One2many('agro.sale.wizard.line', 'wizard_id', string='Items')
    total_amount = fields.Float(compute='_compute_total', string='Total Amount')

    @api.model
    def default_get(self, fields_list):
        # Pre-fills Walk-in Customer from shop config so operator doesn't have to pick one
        res = super().default_get(fields_list)
        config = self.env['inventory.config'].search([], limit=1)
        if config and config.default_walkin_partner_id:
            res['customer_id'] = config.default_walkin_partner_id.id
        return res

    @api.depends('line_ids.subtotal')
    def _compute_total(self):
        for w in self:
            w.total_amount = sum(w.line_ids.mapped('subtotal'))

    def action_confirm(self):
        # Creates sale.order → confirms it → assigns lots to delivery → validates → prints receipt
        self.ensure_one()
        if not self.line_ids:
            raise UserError('Add at least one item.')

        # Early stock availability check — prevents partial confirmation on overcommit
        for line in self.line_ids:
            if line.lot_id and line.uom_id and line.product_id:
                qty_in_base = line.uom_id._compute_quantity(line.quantity, line.product_id.uom_id)
                if qty_in_base > line.lot_id.product_qty:
                    raise UserError(
                        f"Not enough stock for {line.product_id.name} in batch {line.lot_id.name}. "
                        f"Requested: {line.quantity:g} {line.uom_id.name} "
                        f"({qty_in_base:.3f} {line.product_id.uom_id.name}), "
                        f"Available: {line.lot_id.product_qty:.3f} {line.product_id.uom_id.name}."
                    )

        order_lines = [(0, 0, {
            'product_id': line.product_product_id.id,
            'product_uom': line.product_id.uom_id.id,
            'product_uom_qty': line.uom_id._compute_quantity(line.quantity, line.product_id.uom_id),
            'price_unit': line.unit_price,
            'discount': line.discount_pct,
            'agro_lot_id': line.lot_id.id if line.lot_id else False,
            'agro_sold_qty': line.quantity,
            'agro_sold_uom_id': line.uom_id.id,
        }) for line in self.line_ids]

        sale_order = self.env['sale.order'].create({
            'partner_id': self.customer_id.id,
            'date_order': fields.Datetime.now(),
            'agro_payment_method': self.payment_method,
            'agro_is_shop_sale': True,
            'note': self.notes or '',
            'order_line': order_lines,
        })
        sale_order.action_confirm()

        for picking in sale_order.picking_ids:
            for move in picking.move_ids:
                wizard_line = self.line_ids.filtered(
                    lambda l: l.product_product_id.id == move.product_id.id
                )[:1]
                if wizard_line and wizard_line.lot_id and move.product_id.tracking == 'lot':
                    # Replace Odoo's auto move lines with our specific lot assignment
                    qty_done = wizard_line.uom_id._compute_quantity(wizard_line.quantity, move.product_uom)
                    move.move_line_ids.unlink()
                    self.env['stock.move.line'].create({
                        'move_id': move.id,
                        'picking_id': picking.id,
                        'product_id': move.product_id.id,
                        'product_uom_id': move.product_uom.id,
                        'lot_id': wizard_line.lot_id.id,
                        'qty_done': qty_done,
                        'location_id': move.location_id.id,
                        'location_dest_id': move.location_dest_id.id,
                    })
                elif wizard_line:
                    move.quantity_done = wizard_line.uom_id._compute_quantity(
                        wizard_line.quantity, move.product_uom
                    )
            # skip_backorder prevents Odoo's backorder popup from interrupting the flow
            picking.with_context(skip_backorder=True, skip_sms=True).button_validate()

        return self.env.ref('inventory_management.report_agro_sale_receipt').report_action(sale_order)


class AgroSaleWizardLine(models.TransientModel):
    # One item row in the sale wizard
    _name = 'agro.sale.wizard.line'
    _description = 'Sale Item'

    wizard_id = fields.Many2one('agro.sale.wizard', string='Wizard')
    product_id = fields.Many2one(
        'product.template', string='Product',
        domain=[('is_sellable', '=', True)], required=True
    )
    # Resolved to product.product because stock.lot and stock.move use variants, not templates
    product_product_id = fields.Many2one(
        'product.product', compute='_compute_product_product', store=True
    )
    lot_id = fields.Many2one(
        'stock.lot', string='Batch',
        domain="[('product_id', '=', product_product_id), ('product_qty', '>', 0)]"
    )
    uom_id = fields.Many2one('uom.uom', string='Unit')
    product_uom_id = fields.Many2one('uom.uom', related='product_id.uom_id', readonly=True, string='Base Unit')
    product_uom_category_id = fields.Many2one('uom.category', related='product_id.uom_id.category_id', string='UoM Category')
    available_qty = fields.Float(compute='_compute_available_qty', string='Available')
    quantity = fields.Float(string='Qty', default=1.0)
    unit_price = fields.Float(string='Price')
    discount_pct = fields.Float(string='Discount %')
    subtotal = fields.Float(compute='_compute_subtotal', string='Subtotal')

    @api.depends('product_id')
    def _compute_product_product(self):
        for line in self:
            line.product_product_id = line.product_id.product_variant_ids[:1] if line.product_id else False

    @api.depends('lot_id.product_qty', 'uom_id', 'product_id')
    def _compute_available_qty(self):
        for line in self:
            if line.lot_id and line.uom_id and line.product_id:
                line.available_qty = line.product_id.uom_id._compute_quantity(
                    line.lot_id.product_qty, line.uom_id
                )
            elif line.lot_id:
                line.available_qty = line.lot_id.product_qty
            else:
                line.available_qty = 0.0

    @api.onchange('product_id')
    def _onchange_product_id(self):
        # FIFO: auto-picks oldest batch with stock — sell expiring stock first
        if not self.product_id:
            return
        lots = self.env['stock.lot'].search([
            ('product_id', 'in', self.product_id.product_variant_ids.ids),
            ('product_qty', '>', 0),
        ], order='expiration_date asc')
        self.lot_id = lots[:1]
        self.unit_price = self.product_id.list_price
        self.uom_id = self.product_id.uom_id

    @api.onchange('uom_id')
    def _onchange_uom_id(self):
        self.quantity = 1.0

    @api.constrains('product_id', 'uom_id')
    def _check_uom_category(self):
        for line in self:
            if line.product_id and line.uom_id:
                if line.uom_id.category_id != line.product_id.uom_id.category_id:
                    raise UserError(
                        f"Unit '{line.uom_id.name}' is not compatible with base unit '{line.product_id.uom_id.name}'."
                    )

    @api.depends('quantity', 'uom_id', 'unit_price', 'discount_pct', 'product_id')
    def _compute_subtotal(self):
        for line in self:
            if line.product_id and line.uom_id:
                qty_in_base = line.uom_id._compute_quantity(line.quantity, line.product_id.uom_id)
                line.subtotal = qty_in_base * line.unit_price * (1 - line.discount_pct / 100)
            else:
                line.subtotal = 0.0
