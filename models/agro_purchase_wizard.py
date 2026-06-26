# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class AgroPurchaseWizard(models.TransientModel):
    # Temporary receive-stock form — creates a real purchase.order and validates the receipt
    _name = 'agro.purchase.wizard'
    _description = 'Receive Stock'

    supplier_id = fields.Many2one('res.partner', string='Supplier', required=True)
    date = fields.Date(string='Date Received', default=fields.Date.today, required=True)
    notes = fields.Text(string='Notes')
    line_ids = fields.One2many('agro.purchase.wizard.line', 'wizard_id', string='Items')
    total_amount = fields.Float(compute='_compute_total', string='Total Amount')

    @api.depends('line_ids.subtotal')
    def _compute_total(self):
        for w in self:
            w.total_amount = sum(w.line_ids.mapped('subtotal'))

    def action_receive(self):
        # Creates purchase.order → confirms → creates stock.lot per line → validates receipt → shows notification
        self.ensure_one()
        if not self.line_ids:
            raise UserError(_('Add at least one item.'))

        order_lines = [(0, 0, {
            'product_id': line.product_product_id.id,
            'product_qty': line.quantity,
            'price_unit': line.unit_price,
            'date_planned': self.date,
            'product_uom': line.product_product_id.uom_po_id.id,
            'name': line.product_id.name,
        }) for line in self.line_ids]

        po = self.env['purchase.order'].create({
            'partner_id': self.supplier_id.id,
            'date_order': self.date,
            'notes': self.notes or '',
            'order_line': order_lines,
        })
        po.button_confirm()

        lines_by_product = {line.product_product_id.id: line for line in self.line_ids}
        for picking in po.picking_ids:
            for move in picking.move_ids:
                wizard_line = lines_by_product.get(move.product_id.id)
                if not wizard_line:
                    continue
                if move.product_id.tracking == 'lot':
                    # Create a new batch for this received stock
                    lot = self.env['stock.lot'].create({
                        'name': wizard_line.batch_name,
                        'product_id': wizard_line.product_product_id.id,
                        'company_id': po.company_id.id,
                        'expiration_date': wizard_line.expiry_date or False,
                        'purchase_date': self.date,
                        'unit_price': wizard_line.unit_price,
                    })
                    # Replace Odoo's auto move line with our lot-specific one
                    move.move_line_ids.unlink()
                    self.env['stock.move.line'].create({
                        'move_id': move.id,
                        'picking_id': picking.id,
                        'product_id': move.product_id.id,
                        'product_uom_id': move.product_uom.id,
                        'lot_id': lot.id,
                        'qty_done': wizard_line.quantity,
                        'location_id': move.location_id.id,
                        'location_dest_id': move.location_dest_id.id,
                    })
                else:
                    move.quantity_done = wizard_line.quantity
            # skip_backorder prevents Odoo's backorder popup
            picking.with_context(skip_backorder=True, skip_sms=True).button_validate()

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Stock Received',
                'message': f'Purchase {po.name} done. Stock updated.',
                'type': 'success',
                'sticky': False,
                'next': {'type': 'ir.actions.act_window_close'},
            }
        }


class AgroPurchaseWizardLine(models.TransientModel):
    # One item row in the purchase wizard
    _name = 'agro.purchase.wizard.line'
    _description = 'Purchase Item'

    wizard_id = fields.Many2one('agro.purchase.wizard', string='Wizard')
    product_id = fields.Many2one(
        'product.template', string='Product',
        domain=[('is_purchasable', '=', True)], required=True
    )
    # Resolved to product.product for stock operations
    product_product_id = fields.Many2one(
        'product.product', compute='_compute_product_product', store=True
    )
    quantity = fields.Float(string='Qty', default=1.0)
    unit_price = fields.Float(string='Cost Price')
    expiry_date = fields.Date(string='Expiry Date')
    batch_name = fields.Char(string='Batch No')  # auto-generated, operator can override
    subtotal = fields.Float(compute='_compute_subtotal', string='Subtotal')

    @api.depends('product_id')
    def _compute_product_product(self):
        for line in self:
            line.product_product_id = line.product_id.product_variant_ids[:1] if line.product_id else False

    @api.onchange('product_id')
    def _onchange_product_id(self):
        # Auto-generates batch number and fills supplier from product default
        if not self.product_id:
            return
        self.batch_name = self.env['ir.sequence'].next_by_code('agro.batch')
        if self.product_id.default_supplier_id and not self.wizard_id.supplier_id:
            self.wizard_id.supplier_id = self.product_id.default_supplier_id

    @api.depends('quantity', 'unit_price')
    def _compute_subtotal(self):
        for line in self:
            line.subtotal = line.quantity * line.unit_price

    @api.constrains('quantity', 'unit_price')
    def _check_line_values(self):
        for line in self:
            if line.quantity <= 0:
                raise UserError(_('Quantity must be greater than zero.'))
            if line.unit_price < 0:
                raise UserError(_('Cost price cannot be negative.'))
