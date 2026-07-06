# -*- coding: utf-8 -*-
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta
from odoo import models, fields, api


class AgroDashboard(models.AbstractModel):
    """
    Stateless KPI engine for the business dashboard.
    All methods are @api.model — no records, no state.
    Returns plain dicts (JSON-serializable) consumed by the OWL frontend via controller.
    """
    _name = 'agro.dashboard'
    _description = 'Agro Dashboard KPI Engine'

    # ─── helpers ────────────────────────────────────────────────────────────────

    @api.model
    def _shop_sale_domain(self, date_from=None, date_to=None, extra=None):
        domain = [('agro_is_shop_sale', '=', True), ('state', 'in', ['sale', 'done'])]
        if date_from:
            domain.append(('date_order', '>=', str(date_from) + ' 00:00:00'))
        if date_to:
            domain.append(('date_order', '<=', str(date_to) + ' 23:59:59'))
        if extra:
            domain += extra
        return domain

    @api.model
    def _sum_orders(self, domain):
        """Returns (total_sales, total_profit, total_cost) for matching orders."""
        orders = self.env['sale.order'].search(domain)
        sales = sum(orders.mapped('amount_total'))
        profit = sum(orders.mapped('agro_total_profit'))
        cost = sum(orders.mapped('agro_cost_total'))
        return sales, profit, cost

    @api.model
    def _growth(self, current, previous):
        """Returns growth percentage rounded to 2dp. None if previous is 0."""
        if previous:
            return round((current - previous) / previous * 100, 2)
        return None

    # ─── Section 1: Sales KPIs ──────────────────────────────────────────────────

    @api.model
    def get_sales_kpis(self):
        today = date.today()
        yesterday = today - timedelta(days=1)
        month_start = today.replace(day=1)
        last_month_start = (month_start - timedelta(days=1)).replace(day=1)
        last_month_end = month_start - timedelta(days=1)
        year_start = today.replace(month=1, day=1)
        last_year_start = year_start - relativedelta(years=1)
        last_year_end = year_start - timedelta(days=1)

        today_sales, _, _ = self._sum_orders(self._shop_sale_domain(today, today))
        yest_sales, _, _ = self._sum_orders(self._shop_sale_domain(yesterday, yesterday))
        month_sales, _, _ = self._sum_orders(self._shop_sale_domain(month_start, today))
        last_month_sales, _, _ = self._sum_orders(self._shop_sale_domain(last_month_start, last_month_end))
        year_sales, _, _ = self._sum_orders(self._shop_sale_domain(year_start, today))
        last_year_sales, _, _ = self._sum_orders(self._shop_sale_domain(last_year_start, last_year_end))
        lifetime_sales, _, _ = self._sum_orders(self._shop_sale_domain())

        return {
            'today': today_sales,
            'yesterday': yest_sales,
            'today_vs_yesterday_pct': self._growth(today_sales, yest_sales),
            'this_month': month_sales,
            'last_month': last_month_sales,
            'month_vs_last_month_pct': self._growth(month_sales, last_month_sales),
            'this_year': year_sales,
            'last_year': last_year_sales,
            'year_vs_last_year_pct': self._growth(year_sales, last_year_sales),
            'lifetime': lifetime_sales,
        }

    # ─── Section 2: Profit KPIs ─────────────────────────────────────────────────

    @api.model
    def get_profit_kpis(self):
        today = date.today()
        month_start = today.replace(day=1)
        year_start = today.replace(month=1, day=1)

        _, today_profit, _ = self._sum_orders(self._shop_sale_domain(today, today))
        _, month_profit, _ = self._sum_orders(self._shop_sale_domain(month_start, today))
        _, year_profit, _ = self._sum_orders(self._shop_sale_domain(year_start, today))
        _, lifetime_profit, _ = self._sum_orders(self._shop_sale_domain())

        return {
            'today': today_profit,
            'this_month': month_profit,
            'this_year': year_profit,
            'lifetime': lifetime_profit,
        }

    # ─── Section 3: Cost Price Analysis ─────────────────────────────────────────

    @api.model
    def get_cost_analysis(self):
        today = date.today()
        month_start = today.replace(day=1)
        year_start = today.replace(month=1, day=1)

        month_sales, month_profit, month_cost = self._sum_orders(self._shop_sale_domain(month_start, today))
        year_sales, year_profit, year_cost = self._sum_orders(self._shop_sale_domain(year_start, today))
        life_sales, life_profit, life_cost = self._sum_orders(self._shop_sale_domain())

        def margin(sales, profit):
            return round(profit / sales * 100, 2) if sales else 0.0

        return {
            'month': {'sales': month_sales, 'cost': month_cost, 'profit': month_profit, 'margin_pct': margin(month_sales, month_profit)},
            'year': {'sales': year_sales, 'cost': year_cost, 'profit': year_profit, 'margin_pct': margin(year_sales, year_profit)},
            'lifetime': {'sales': life_sales, 'cost': life_cost, 'profit': life_profit, 'margin_pct': margin(life_sales, life_profit)},
        }

    # ─── Section 4: Outstanding Analysis ────────────────────────────────────────

    @api.model
    def get_outstanding_analysis(self):
        SaleOrder = self.env['sale.order']
        open_orders = SaleOrder.search([
            ('agro_is_shop_sale', '=', True),
            ('agro_amount_outstanding', '>', 0.005),
        ])
        total_outstanding = sum(open_orders.mapped('agro_amount_outstanding'))
        overdue_orders = open_orders.filtered('agro_is_overdue')
        overdue_amount = sum(overdue_orders.mapped('agro_amount_outstanding'))
        # Recoverable = outstanding within credit period (not yet overdue)
        recoverable = total_outstanding - overdue_amount
        # Cost yet to be recovered = cost of goods in outstanding orders (not yet collected)
        cost_unrec = sum(open_orders.mapped('agro_cost_total')) - sum(open_orders.mapped('agro_amount_paid'))
        # Clamp to 0 — if paid > cost, we've recovered cost regardless of outstanding balance
        cost_unrec = max(0.0, cost_unrec)

        return {
            'total_outstanding': total_outstanding,
            'overdue': overdue_amount,
            'recoverable': recoverable,
            'cost_yet_to_recover': cost_unrec,
        }

    # ─── Section 5: Invoice Summary ──────────────────────────────────────────────

    @api.model
    def get_invoice_summary(self):
        today = date.today()
        today_orders = self.env['sale.order'].search(
            self._shop_sale_domain(today, today)
        )
        totals = [o.amount_total for o in today_orders]
        count = len(totals)
        return {
            'total_invoices': count,
            'avg_bill_value': round(sum(totals) / count, 2) if count else 0.0,
            'highest_bill': max(totals) if totals else 0.0,
            'lowest_bill': min(totals) if totals else 0.0,
        }

    # ─── Section 6: Payment Summary ──────────────────────────────────────────────

    @api.model
    def get_payment_summary(self, date_from=None, date_to=None):
        today = date.today()
        df = date_from or today.replace(day=1)
        dt = date_to or today
        orders = self.env['sale.order'].search(self._shop_sale_domain(df, dt))
        summary = {'cash': 0.0, 'upi': 0.0, 'bank_transfer': 0.0, 'credit': 0.0, 'other': 0.0}
        for o in orders:
            method = o.agro_payment_method or 'other'
            summary[method] = summary.get(method, 0.0) + o.amount_total
        return summary

    # ─── Section 7: Top Performing Categories ────────────────────────────────────

    @api.model
    def get_category_performance(self, date_from=None, date_to=None):
        today = date.today()
        df = date_from or today.replace(day=1)
        dt = date_to or today
        self.env.cr.execute(
            """
            SELECT
                ic.id                               AS category_id,
                ic.name                             AS category,
                SUM(sol.price_subtotal)             AS sales,
                SUM(sol.agro_profit)                AS profit,
                SUM(sol.product_uom_qty)            AS qty_sold
            FROM sale_order_line sol
            JOIN sale_order so   ON so.id  = sol.order_id
            JOIN product_product pp ON pp.id = sol.product_id
            JOIN product_template pt ON pt.id = pp.product_tmpl_id
            LEFT JOIN inventory_category ic ON ic.id = pt.agro_category_id
            WHERE so.agro_is_shop_sale = TRUE
              AND so.state IN ('sale','done')
              AND so.date_order::date BETWEEN %s AND %s
            GROUP BY ic.id, ic.name
            ORDER BY sales DESC
            """,
            [df, dt]
        )
        rows = self.env.cr.dictfetchall()
        return rows

    # ─── Section 8: Top Selling Products ─────────────────────────────────────────

    @api.model
    def get_top_products(self, limit=10, date_from=None, date_to=None, order_by='sales'):
        today = date.today()
        df = date_from or today.replace(day=1)
        dt = date_to or today
        order_col = 'sales' if order_by == 'sales' else 'profit'
        self.env.cr.execute(
            f"""
            SELECT
                pt.id                               AS product_id,
                pt.name->>'en_US'                   AS product_name,
                SUM(sol.price_subtotal)             AS sales,
                SUM(sol.agro_profit)                AS profit,
                SUM(sol.product_uom_qty)            AS qty_sold
            FROM sale_order_line sol
            JOIN sale_order so      ON so.id  = sol.order_id
            JOIN product_product pp ON pp.id  = sol.product_id
            JOIN product_template pt ON pt.id = pp.product_tmpl_id
            WHERE so.agro_is_shop_sale = TRUE
              AND so.state IN ('sale','done')
              AND so.date_order::date BETWEEN %s AND %s
            GROUP BY pt.id, pt.name
            ORDER BY {order_col} DESC
            LIMIT %s
            """,
            [df, dt, limit]
        )
        return self.env.cr.dictfetchall()

    # ─── Section 9: Low/Dead Stock ────────────────────────────────────────────────

    @api.model
    def get_low_stock_products(self):
        products = self.env['product.template'].search([
            ('stock_status', 'in', ['low', 'out']),
            ('is_sellable', '=', True),
        ])
        return [{
            'id': p.id,
            'name': p.name,
            'category': p.agro_category_id.name or '',
            'qty_available': p.qty_available,
            'min_stock': p.min_stock,
            'status': p.stock_status,
        } for p in products]

    @api.model
    def get_dead_stock_products(self, months=3):
        products = self.env['product.template'].search([
            ('agro_dead_stock_months', '>=', months),
            ('qty_available', '>', 0),
            ('is_sellable', '=', True),
        ])
        return [{
            'id': p.id,
            'name': p.name,
            'category': p.agro_category_id.name or '',
            'qty_available': p.qty_available,
            'dead_stock_months': p.agro_dead_stock_months,
            'last_sold': fields.Date.to_string(p.agro_last_sold_date) if p.agro_last_sold_date else None,
        } for p in products]

    # ─── Section 10: Sales Trend ──────────────────────────────────────────────────

    @api.model
    def get_sales_trend(self, period='monthly'):
        """
        period: 'daily' (last 30 days), 'monthly' (last 12 months), 'yearly' (last 5 years)
        Returns list of {label, sales, profit} dicts ordered ascending by date.
        """
        today = date.today()
        if period == 'daily':
            self.env.cr.execute(
                """
                SELECT
                    so.date_order::date                 AS label,
                    SUM(so.amount_total)                AS sales,
                    SUM(so.agro_total_profit)           AS profit
                FROM sale_order so
                WHERE so.agro_is_shop_sale = TRUE
                  AND so.state IN ('sale','done')
                  AND so.date_order::date >= %s
                GROUP BY so.date_order::date
                ORDER BY label
                """,
                [today - timedelta(days=30)]
            )
        elif period == 'monthly':
            self.env.cr.execute(
                """
                SELECT
                    TO_CHAR(so.date_order, 'YYYY-MM')   AS label,
                    SUM(so.amount_total)                AS sales,
                    SUM(so.agro_total_profit)           AS profit
                FROM sale_order so
                WHERE so.agro_is_shop_sale = TRUE
                  AND so.state IN ('sale','done')
                  AND so.date_order >= %s
                GROUP BY TO_CHAR(so.date_order, 'YYYY-MM')
                ORDER BY label
                """,
                [today - relativedelta(months=12)]
            )
        else:  # yearly
            self.env.cr.execute(
                """
                SELECT
                    EXTRACT(YEAR FROM so.date_order)::int AS label,
                    SUM(so.amount_total)                  AS sales,
                    SUM(so.agro_total_profit)             AS profit
                FROM sale_order so
                WHERE so.agro_is_shop_sale = TRUE
                  AND so.state IN ('sale','done')
                  AND so.date_order >= %s
                GROUP BY EXTRACT(YEAR FROM so.date_order)
                ORDER BY label
                """,
                [today - relativedelta(years=5)]
            )
        rows = self.env.cr.dictfetchall()
        return [{'label': str(r['label']), 'sales': float(r['sales'] or 0), 'profit': float(r['profit'] or 0)} for r in rows]

    # ─── Section 11: Business Comparison ─────────────────────────────────────────

    @api.model
    def get_mom_comparison(self):
        """Month-over-Month sales and profit comparison."""
        today = date.today()
        cur_start = today.replace(day=1)
        prev_end = cur_start - timedelta(days=1)
        prev_start = prev_end.replace(day=1)

        cur_sales, cur_profit, _ = self._sum_orders(self._shop_sale_domain(cur_start, today))
        prev_sales, prev_profit, _ = self._sum_orders(self._shop_sale_domain(prev_start, prev_end))

        return {
            'current_month': {'sales': cur_sales, 'profit': cur_profit},
            'previous_month': {'sales': prev_sales, 'profit': prev_profit},
            'sales_diff': cur_sales - prev_sales,
            'profit_diff': cur_profit - prev_profit,
            'sales_growth_pct': self._growth(cur_sales, prev_sales),
            'profit_growth_pct': self._growth(cur_profit, prev_profit),
        }

    @api.model
    def get_yoy_comparison(self):
        """Year-over-Year: current year vs previous year, and current month vs same month last year."""
        today = date.today()
        cur_year_start = today.replace(month=1, day=1)
        prev_year_start = cur_year_start - relativedelta(years=1)
        prev_year_end = cur_year_start - timedelta(days=1)

        cur_month_start = today.replace(day=1)
        prev_same_month_start = cur_month_start - relativedelta(years=1)
        prev_same_month_end = prev_same_month_start + relativedelta(months=1) - timedelta(days=1)

        cur_yr_s, cur_yr_p, _ = self._sum_orders(self._shop_sale_domain(cur_year_start, today))
        prev_yr_s, prev_yr_p, _ = self._sum_orders(self._shop_sale_domain(prev_year_start, prev_year_end))
        cur_mo_s, cur_mo_p, _ = self._sum_orders(self._shop_sale_domain(cur_month_start, today))
        prev_mo_s, prev_mo_p, _ = self._sum_orders(self._shop_sale_domain(prev_same_month_start, prev_same_month_end))

        return {
            'annual': {
                'current_year': {'sales': cur_yr_s, 'profit': cur_yr_p},
                'previous_year': {'sales': prev_yr_s, 'profit': prev_yr_p},
                'sales_diff': cur_yr_s - prev_yr_s,
                'profit_diff': cur_yr_p - prev_yr_p,
                'sales_growth_pct': self._growth(cur_yr_s, prev_yr_s),
                'profit_growth_pct': self._growth(cur_yr_p, prev_yr_p),
            },
            'same_month': {
                'current': {'sales': cur_mo_s, 'profit': cur_mo_p},
                'previous': {'sales': prev_mo_s, 'profit': prev_mo_p},
                'sales_diff': cur_mo_s - prev_mo_s,
                'profit_diff': cur_mo_p - prev_mo_p,
                'sales_growth_pct': self._growth(cur_mo_s, prev_mo_s),
                'profit_growth_pct': self._growth(cur_mo_p, prev_mo_p),
            },
        }

    @api.model
    def get_best_months(self):
        """Identify the highest sales month and highest profit month of all time."""
        self.env.cr.execute(
            """
            SELECT
                TO_CHAR(date_order, 'Month YYYY')   AS month_label,
                SUM(amount_total)                   AS total_sales,
                SUM(agro_total_profit)              AS total_profit
            FROM sale_order
            WHERE agro_is_shop_sale = TRUE AND state IN ('sale','done')
            GROUP BY TO_CHAR(date_order, 'Month YYYY'), DATE_TRUNC('month', date_order)
            ORDER BY total_sales DESC
            LIMIT 1
            """
        )
        best_sales_row = self.env.cr.fetchone()
        self.env.cr.execute(
            """
            SELECT
                TO_CHAR(date_order, 'Month YYYY')   AS month_label,
                SUM(amount_total)                   AS total_sales,
                SUM(agro_total_profit)              AS total_profit
            FROM sale_order
            WHERE agro_is_shop_sale = TRUE AND state IN ('sale','done')
            GROUP BY TO_CHAR(date_order, 'Month YYYY'), DATE_TRUNC('month', date_order)
            ORDER BY total_profit DESC
            LIMIT 1
            """
        )
        best_profit_row = self.env.cr.fetchone()
        return {
            'best_sales_month': {
                'label': best_sales_row[0].strip() if best_sales_row else None,
                'amount': float(best_sales_row[1] or 0) if best_sales_row else 0,
            },
            'best_profit_month': {
                'label': best_profit_row[0].strip() if best_profit_row else None,
                'amount': float(best_profit_row[2] or 0) if best_profit_row else 0,
            },
        }

    # ─── Section 12: Village Sales ────────────────────────────────────────────────

    @api.model
    def get_village_sales(self, date_from=None, date_to=None):
        today = date.today()
        df = date_from or today.replace(day=1)
        dt = date_to or today
        self.env.cr.execute(
            """
            SELECT
                av.name                             AS village,
                SUM(so.amount_total)                AS sales,
                SUM(so.agro_total_profit)           AS profit,
                COUNT(DISTINCT so.partner_id)       AS customers
            FROM sale_order so
            JOIN res_partner rp ON rp.id = so.partner_id
            JOIN agro_village av ON av.id = rp.village_id
            WHERE so.agro_is_shop_sale = TRUE
              AND so.state IN ('sale','done')
              AND so.date_order::date BETWEEN %s AND %s
            GROUP BY av.name
            ORDER BY sales DESC
            """,
            [df, dt]
        )
        return self.env.cr.dictfetchall()

    # ─── Section 13: Stock Valuation ─────────────────────────────────────────────

    @api.model
    def get_stock_valuation(self):
        self.env.cr.execute(
            """
            SELECT
                COUNT(DISTINCT sl.product_id)           AS total_products,
                SUM(sl.product_qty * sl.unit_price)     AS purchase_value,
                SUM(sl.product_qty * pt.list_price)     AS selling_value
            FROM stock_lot sl
            JOIN product_product pp ON pp.id = sl.product_id
            JOIN product_template pt ON pt.id = pp.product_tmpl_id
            WHERE sl.product_qty > 0
            """
        )
        row = self.env.cr.fetchone()
        purchase_val = float(row[1] or 0)
        selling_val = float(row[2] or 0)
        return {
            'total_products': int(row[0] or 0),
            'purchase_value': purchase_val,
            'selling_value': selling_val,
            'estimated_profit': selling_val - purchase_val,
        }

    # ─── Section 14: Expiry Analysis ─────────────────────────────────────────────

    @api.model
    def get_expiry_analysis(self):
        today = date.today()
        d30 = today + timedelta(days=30)
        d90 = today + timedelta(days=90)
        lots = self.env['stock.lot'].search([('product_qty', '>', 0)])
        expired = lots.filtered(lambda l: l.expiration_date and l.expiration_date < today)
        exp_30 = lots.filtered(lambda l: l.expiration_date and today <= l.expiration_date <= d30)
        exp_90 = lots.filtered(lambda l: l.expiration_date and d30 < l.expiration_date <= d90)
        safe = lots.filtered(lambda l: not l.expiration_date or l.expiration_date > d90)
        return {
            'expired': len(expired),
            'expiring_30': len(exp_30),
            'expiring_90': len(exp_90),
            'safe': len(safe),
        }

    # ─── Section 15: Date-to-Date Report ─────────────────────────────────────────

    @api.model
    def get_date_range_report(self, date_from, date_to):
        """Full sales + profit report for an arbitrary date range."""
        df = fields.Date.from_string(date_from)
        dt = fields.Date.from_string(date_to)
        sales, profit, cost = self._sum_orders(self._shop_sale_domain(df, dt))
        trend = self.get_sales_trend.__func__  # avoid re-query; use raw SQL below
        self.env.cr.execute(
            """
            SELECT
                so.date_order::date                 AS label,
                SUM(so.amount_total)                AS sales,
                SUM(so.agro_total_profit)           AS profit,
                COUNT(so.id)                        AS invoices,
                COUNT(DISTINCT so.partner_id)       AS customers
            FROM sale_order so
            WHERE so.agro_is_shop_sale = TRUE
              AND so.state IN ('sale','done')
              AND so.date_order::date BETWEEN %s AND %s
            GROUP BY so.date_order::date
            ORDER BY label
            """,
            [df, dt]
        )
        daily = [
            {
                'date': str(r[0]),
                'sales': float(r[1] or 0),
                'profit': float(r[2] or 0),
                'invoices': int(r[3] or 0),
                'customers': int(r[4] or 0),
            }
            for r in self.env.cr.fetchall()
        ]
        return {
            'date_from': str(df),
            'date_to': str(dt),
            'total_sales': sales,
            'total_profit': profit,
            'total_cost': cost,
            'profit_margin_pct': round(profit / sales * 100, 2) if sales else 0.0,
            'daily': daily,
        }

    # ─── Section 16: Quick Summary (dashboard top cards) ─────────────────────────

    @api.model
    def get_quick_summary(self):
        today = date.today()
        month_start = today.replace(day=1)

        today_sales, today_profit, _ = self._sum_orders(self._shop_sale_domain(today, today))
        month_sales, month_profit, _ = self._sum_orders(self._shop_sale_domain(month_start, today))

        outstanding = self.get_outstanding_analysis()
        stock_val = self.get_stock_valuation()
        invoice_sum = self.get_invoice_summary()

        low_stock_count = self.env['product.template'].search_count([
            ('stock_status', 'in', ['low', 'out']), ('is_sellable', '=', True)
        ])
        expiring_count = self.env['stock.lot'].search_count([
            ('expiry_status', 'in', ['expiring', 'expired']), ('product_qty', '>', 0)
        ])
        customer_count = self.env['res.partner'].search_count([
            ('sale_order_ids.agro_is_shop_sale', '=', True)
        ])
        product_count = self.env['product.template'].search_count([('is_sellable', '=', True)])
        today_customer_count = len(self.env['sale.order'].search(
            self._shop_sale_domain(today, today)
        ).mapped('partner_id'))

        return {
            'today_sales': today_sales,
            'today_profit': today_profit,
            'today_customers': today_customer_count,
            'today_invoices': invoice_sum['total_invoices'],
            'month_sales': month_sales,
            'month_profit': month_profit,
            'outstanding': outstanding['total_outstanding'],
            'overdue': outstanding['overdue'],
            'cost_yet_to_recover': outstanding['cost_yet_to_recover'],
            'stock_value': stock_val['purchase_value'],
            'low_stock_products': low_stock_count,
            'expiring_products': expiring_count,
            'total_customers': customer_count,
            'total_products': product_count,
        }

    # ─── Cron: refresh stored computed fields on product ─────────────────────────

    @api.model
    def _cron_refresh_product_stats(self):
        """Nightly: force-recompute stored analytics fields on all sellable products."""
        products = self.env['product.template'].search([('is_sellable', '=', True)])
        products._compute_agro_purchase_stats()
        products._compute_agro_sold_stats()
        products._compute_agro_reorder()
