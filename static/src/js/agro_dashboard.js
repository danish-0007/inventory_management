/** @odoo-module **/

import { Component, useState, onMounted, onWillUnmount } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

// ─── Utility helpers ─────────────────────────────────────────────────────────

function fmt(val, decimals = 0) {
    if (val === null || val === undefined) return "—";
    const num = parseFloat(val);
    if (isNaN(num)) return "—";
    return "₹" + num.toLocaleString("en-IN", { minimumFractionDigits: decimals, maximumFractionDigits: decimals });
}

function fmtQty(val) {
    if (val === null || val === undefined) return "—";
    return parseFloat(val).toLocaleString("en-IN", { maximumFractionDigits: 2 });
}

function growthIcon(pct) {
    if (pct === null || pct === undefined) return "";
    return pct >= 0 ? "🟢 ▲" : "🔴 ▼";
}

function growthClass(pct) {
    if (pct === null || pct === undefined) return "agro-neutral";
    return pct >= 0 ? "agro-growth-up" : "agro-growth-down";
}

async function rpc(url, params = {}) {
    const res = await fetch(url, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ jsonrpc: "2.0", method: "call", id: 1, params }),
    });
    const data = await res.json();
    return data.result;
}

// ─── Chart helper (Chart.js loaded via CDN in template) ──────────────────────

function destroyChart(chartRef) {
    if (chartRef && chartRef._chart) {
        chartRef._chart.destroy();
        chartRef._chart = null;
    }
}

function makeLineChart(canvasId, labels, datasets) {
    const ctx = document.getElementById(canvasId);
    if (!ctx) return null;
    return new Chart(ctx, {
        type: "line",
        data: { labels, datasets },
        options: {
            responsive: true,
            plugins: { legend: { position: "top" } },
            scales: { y: { beginAtZero: true } },
        },
    });
}

function makeBarChart(canvasId, labels, datasets, horizontal = false) {
    const ctx = document.getElementById(canvasId);
    if (!ctx) return null;
    return new Chart(ctx, {
        type: "bar",
        data: { labels, datasets },
        options: {
            indexAxis: horizontal ? "y" : "x",
            responsive: true,
            plugins: { legend: { position: "top" } },
            scales: { x: { beginAtZero: true } },
        },
    });
}

function makePieChart(canvasId, labels, data, colors) {
    const ctx = document.getElementById(canvasId);
    if (!ctx) return null;
    return new Chart(ctx, {
        type: "pie",
        data: {
            labels,
            datasets: [{ data, backgroundColor: colors }],
        },
        options: { responsive: true, plugins: { legend: { position: "right" } } },
    });
}

const PIE_COLORS = ["#4f46e5", "#10b981", "#f59e0b", "#ef4444", "#8b5cf6", "#06b6d4"];

// ─── Main Dashboard Component ────────────────────────────────────────────────

export class AgroDashboard extends Component {
    static template = "inventory_management.AgroDashboard";

    setup() {
        this.state = useState({
            loading: true,
            activeTab: "overview",
            summary: {},
            salesKpis: {},
            profitKpis: {},
            costAnalysis: {},
            outstanding: {},
            invoiceSummary: {},
            paymentSummary: {},
            categoryPerf: [],
            topProducts: [],
            topProfitProducts: [],
            lowStock: [],
            salesTrend: [],
            momComparison: {},
            yoyComparison: {},
            bestMonths: {},
            villageSales: [],
            stockValuation: {},
            expiryAnalysis: {},
            deadStock: [],
            dateFrom: new Date(new Date().getFullYear(), new Date().getMonth(), 1).toISOString().slice(0, 10),
            dateTo: new Date().toISOString().slice(0, 10),
            dateRangeResult: null,
            trendPeriod: "monthly",
        });
        this._charts = {};
        onMounted(() => this._loadAll());
        onWillUnmount(() => Object.values(this._charts).forEach(destroyChart));
    }

    async _loadAll() {
        this.state.loading = true;
        const [
            summary, salesKpis, profitKpis, costAnalysis, outstanding,
            invoiceSummary, paymentSummary, categoryPerf, topProducts,
            topProfitProducts, lowStock, salesTrend, momComparison,
            yoyComparison, bestMonths, villageSales, stockValuation,
            expiryAnalysis, deadStock,
        ] = await Promise.all([
            rpc("/agro/dashboard/quick_summary"),
            rpc("/agro/dashboard/sales_kpis"),
            rpc("/agro/dashboard/profit_kpis"),
            rpc("/agro/dashboard/cost_analysis"),
            rpc("/agro/dashboard/outstanding"),
            rpc("/agro/dashboard/invoice_summary"),
            rpc("/agro/dashboard/payment_summary"),
            rpc("/agro/dashboard/category_performance"),
            rpc("/agro/dashboard/top_products", { order_by: "sales" }),
            rpc("/agro/dashboard/top_products", { order_by: "profit" }),
            rpc("/agro/dashboard/low_stock"),
            rpc("/agro/dashboard/sales_trend", { period: "monthly" }),
            rpc("/agro/dashboard/mom_comparison"),
            rpc("/agro/dashboard/yoy_comparison"),
            rpc("/agro/dashboard/best_months"),
            rpc("/agro/dashboard/village_sales"),
            rpc("/agro/dashboard/stock_valuation"),
            rpc("/agro/dashboard/expiry_analysis"),
            rpc("/agro/dashboard/dead_stock", { months: 3 }),
        ]);
        Object.assign(this.state, {
            summary, salesKpis, profitKpis, costAnalysis, outstanding,
            invoiceSummary, paymentSummary, categoryPerf, topProducts,
            topProfitProducts, lowStock, salesTrend, momComparison,
            yoyComparison, bestMonths, villageSales, stockValuation,
            expiryAnalysis, deadStock, loading: false,
        });
        // Render charts after DOM update
        setTimeout(() => this._renderCharts(), 100);
    }

    async _loadTrend() {
        const salesTrend = await rpc("/agro/dashboard/sales_trend", { period: this.state.trendPeriod });
        this.state.salesTrend = salesTrend;
        setTimeout(() => this._renderTrendChart(), 50);
    }

    async loadDateRange() {
        if (!this.state.dateFrom || !this.state.dateTo) return;
        const result = await rpc("/agro/dashboard/date_range_report", {
            date_from: this.state.dateFrom,
            date_to: this.state.dateTo,
        });
        this.state.dateRangeResult = result;
        setTimeout(() => this._renderDateRangeChart(), 50);
    }

    setTab(tab) {
        this.state.activeTab = tab;
        setTimeout(() => this._renderCharts(), 150);
    }

    setTrendPeriod(period) {
        this.state.trendPeriod = period;
        this._loadTrend();
    }

    _renderCharts() {
        const tab = this.state.activeTab;
        if (tab === "charts" || tab === "overview") this._renderTrendChart();
        if (tab === "charts") {
            this._renderCategoryPieChart();
            this._renderTopProductsChart();
            this._renderPaymentPieChart();
            this._renderOutstandingPieChart();
            this._renderVillageSalesChart();
            this._renderExpiryPieChart();
        }
        if (tab === "comparison") this._renderComparisonChart();
    }

    _renderTrendChart() {
        if (this._charts.trend) { this._charts.trend.destroy(); }
        const trend = this.state.salesTrend;
        if (!trend || !trend.length) return;
        this._charts.trend = makeLineChart(
            "chart_trend",
            trend.map(r => r.label),
            [
                { label: "Sales (₹)", data: trend.map(r => r.sales), borderColor: "#4f46e5", backgroundColor: "rgba(79,70,229,0.15)", tension: 0.4, fill: true },
                { label: "Profit (₹)", data: trend.map(r => r.profit), borderColor: "#10b981", backgroundColor: "rgba(16,185,129,0.10)", tension: 0.4, fill: true },
            ]
        );
    }

    _renderCategoryPieChart() {
        if (this._charts.catPie) { this._charts.catPie.destroy(); }
        const cats = this.state.categoryPerf;
        if (!cats || !cats.length) return;
        this._charts.catPie = makePieChart(
            "chart_cat_pie",
            cats.map(c => c.category || "Uncategorized"),
            cats.map(c => c.sales),
            PIE_COLORS
        );
    }

    _renderTopProductsChart() {
        if (this._charts.topProd) { this._charts.topProd.destroy(); }
        const prods = this.state.topProducts.slice(0, 10);
        if (!prods || !prods.length) return;
        this._charts.topProd = makeBarChart(
            "chart_top_products",
            prods.map(p => p.product_name),
            [{ label: "Sales (₹)", data: prods.map(p => p.sales), backgroundColor: "#4f46e5" }],
            true
        );
    }

    _renderPaymentPieChart() {
        if (this._charts.payment) { this._charts.payment.destroy(); }
        const pm = this.state.paymentSummary;
        if (!pm) return;
        const labels = ["Cash", "UPI", "Bank Transfer", "Credit", "Other"];
        const vals = [pm.cash || 0, pm.upi || 0, pm.bank_transfer || 0, pm.credit || 0, pm.other || 0];
        this._charts.payment = makePieChart("chart_payment", labels, vals, PIE_COLORS);
    }

    _renderOutstandingPieChart() {
        if (this._charts.outstanding) { this._charts.outstanding.destroy(); }
        const o = this.state.outstanding;
        if (!o) return;
        const paid = (this.state.salesKpis.lifetime || 0) - (o.total_outstanding || 0);
        this._charts.outstanding = makePieChart(
            "chart_outstanding",
            ["Collected", "Outstanding", "Overdue"],
            [Math.max(0, paid), o.total_outstanding - o.overdue, o.overdue],
            ["#10b981", "#f59e0b", "#ef4444"]
        );
    }

    _renderVillageSalesChart() {
        if (this._charts.village) { this._charts.village.destroy(); }
        const vils = this.state.villageSales.slice(0, 10);
        if (!vils || !vils.length) return;
        this._charts.village = makeBarChart(
            "chart_village",
            vils.map(v => v.village),
            [{ label: "Sales (₹)", data: vils.map(v => v.sales), backgroundColor: "#8b5cf6" }],
            true
        );
    }

    _renderExpiryPieChart() {
        if (this._charts.expiry) { this._charts.expiry.destroy(); }
        const e = this.state.expiryAnalysis;
        if (!e) return;
        this._charts.expiry = makePieChart(
            "chart_expiry",
            ["Expired", "Expiring ≤30d", "Expiring ≤90d", "Safe"],
            [e.expired || 0, e.expiring_30 || 0, e.expiring_90 || 0, e.safe || 0],
            ["#ef4444", "#f59e0b", "#f97316", "#10b981"]
        );
    }

    _renderComparisonChart() {
        if (this._charts.compSales) { this._charts.compSales.destroy(); }
        const mom = this.state.momComparison;
        if (!mom || !mom.current_month) return;
        // Placeholder: bar chart showing MoM comparison
        const labels = ["Previous Month", "Current Month"];
        this._charts.compSales = makeBarChart(
            "chart_comparison_sales",
            labels,
            [
                { label: "Sales (₹)", data: [mom.previous_month.sales, mom.current_month.sales], backgroundColor: ["#a5b4fc", "#4f46e5"] },
                { label: "Profit (₹)", data: [mom.previous_month.profit, mom.current_month.profit], backgroundColor: ["#6ee7b7", "#10b981"] },
            ]
        );
    }

    _renderDateRangeChart() {
        if (this._charts.dateRange) { this._charts.dateRange.destroy(); }
        const result = this.state.dateRangeResult;
        if (!result || !result.daily || !result.daily.length) return;
        this._charts.dateRange = makeLineChart(
            "chart_date_range",
            result.daily.map(d => d.date),
            [
                { label: "Sales (₹)", data: result.daily.map(d => d.sales), borderColor: "#4f46e5", tension: 0.4 },
                { label: "Profit (₹)", data: result.daily.map(d => d.profit), borderColor: "#10b981", tension: 0.4 },
            ]
        );
    }

    // ─── Template helpers ─────────────────────────────────────────────────────

    fmt(val) { return fmt(val); }
    fmtQty(val) { return fmtQty(val); }
    growthIcon(pct) { return growthIcon(pct); }
    growthClass(pct) { return growthClass(pct); }
    fmtPct(pct) {
        if (pct === null || pct === undefined) return "N/A";
        const sign = pct >= 0 ? "+" : "";
        return `${sign}${parseFloat(pct).toFixed(2)}%`;
    }
}

// Register as a client action
registry.category("actions").add("agro_business_dashboard", AgroDashboard);
