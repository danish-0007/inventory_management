# -*- coding: utf-8 -*-
from odoo import models, api, fields

class UomUom(models.Model):
    _inherit = 'uom.uom'

    @api.model
    def _setup_agro_uoms(self):
        # 1. Rename standard UoMs
        unit_uom = self.env.ref('uom.product_uom_unit', raise_if_not_found=False)
        if unit_uom:
            unit_uom.write({'name': 'unit'})
            
        kg_uom = self.env.ref('uom.product_uom_kgm', raise_if_not_found=False)
        if kg_uom:
            kg_uom.write({'name': 'kgs'})
            
        gram_uom = self.env.ref('uom.product_uom_gram', raise_if_not_found=False)
        if gram_uom:
            gram_uom.write({'name': 'gm'})
            
        litre_uom = self.env.ref('uom.product_uom_litre', raise_if_not_found=False)
        if litre_uom:
            litre_uom.write({'name': 'ltr'})
            
        # 2. Check/create nos UoM (bigger than unit, factor 1.0)
        nos_uom = self.env.ref('inventory_management.product_uom_nos', raise_if_not_found=False)
        if not nos_uom:
            categ_unit = self.env.ref('uom.product_uom_categ_unit')
            nos_uom = self.env['uom.uom'].create({
                'name': 'nos',
                'category_id': categ_unit.id,
                'uom_type': 'bigger',
                'factor': 1.0,
                'rounding': 1.0,
            })
            self.env['ir.model.data'].create({
                'module': 'inventory_management',
                'name': 'product_uom_nos',
                'model': 'uom.uom',
                'res_id': nos_uom.id,
                'noupdate': True,
            })

        # 3. Archive all other UoMs to show only required ones
        keep_xml_ids = [
            'uom.product_uom_unit',                  # unit
            'inventory_management.product_uom_nos',  # nos
            'uom.product_uom_kgm',                   # kgs
            'uom.product_uom_gram',                  # gm
            'uom.product_uom_litre',                 # ltr
            'inventory_management.product_uom_ml',   # ml
            'inventory_management.uom_pack',
            'inventory_management.uom_bag',
            'inventory_management.uom_bundle',
        ]
        keep_ids = []
        for xml_id in keep_xml_ids:
            rec = self.env.ref(xml_id, raise_if_not_found=False)
            if rec:
                keep_ids.append(rec.id)
                
        # Deactivate others
        self.search([('id', 'not in', keep_ids)]).write({'active': False})
        
        # Ensure our kept ones are active
        self.search([('id', 'in', keep_ids)]).write({'active': True})
