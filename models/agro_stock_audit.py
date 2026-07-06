# -*- coding: utf-8 -*-
from odoo import models, fields, api


class AgroStockAudit(models.Model):
    """
    Immutable stock movement log with user attribution and reason.
    Created automatically by purchase/sale wizards and manually for adjustments.
    Never edited after creation — it is the audit trail.
    """
    _name = 'agro.stock.audit'
    _description = 'Stock Movement Audit'
    _order = 'date desc, id desc'

    date = fields.Datetime(string='Date & Time', default=fields.Datetime.now, required=True)
    user_id = fields.Many2one('res.users', string='User', default=lambda self: self.env.user, required=True)
    product_id = fields.Many2one('product.template', string='Product', required=True, index=True)
    lot_id = fields.Many2one('stock.lot', string='Batch')
    movement_type = fields.Selection([
        ('purchase', 'Purchase / Stock In'),
        ('sale', 'Sale / Stock Out'),
        ('sale_return', 'Sale Return'),
        ('purchase_return', 'Purchase Return'),
        ('adjustment', 'Stock Adjustment'),
        ('damaged', 'Damaged / Written Off'),
        ('expired', 'Expired / Disposed'),
    ], string='Type', required=True, index=True)
    qty_change = fields.Float(
        string='Qty Change',
        help='Positive = stock increased (purchase/return). Negative = stock decreased (sale/write-off).'
    )
    reason = fields.Char(string='Reason / Notes')
    reference = fields.Char(string='Reference', help='Sale order name or purchase order name')

    def write(self, vals):
        # Audit log is immutable. Block edits post-creation.
        raise models.UserError('Stock audit entries cannot be edited. Create a new adjustment entry instead.')

    def unlink(self):
        raise models.UserError('Stock audit entries cannot be deleted.')
