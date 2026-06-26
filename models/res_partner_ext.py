# -*- coding: utf-8 -*-
from odoo import models, fields


class ResPartnerExt(models.Model):
    # Agro fields: village, crops grown, per-customer credit period, field notes
    _inherit = 'res.partner'

    village_id = fields.Many2one('agro.village', string='Village')
    crop_ids = fields.Many2many('agro.crop', string='Crops Grown')
    credit_period = fields.Integer(
        string='Credit Period (Days)',
        default=lambda self: self.env['inventory.config'].get_config().default_credit_period,
        help='Number of days this customer is given to clear a bill before it is marked overdue.'
    )
    note_ids = fields.One2many('agro.customer.note', 'partner_id', string='Notes & Field History')

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
