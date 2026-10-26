// ============================================================
// Sales Data Analysis System - front-end application logic
// ============================================================

const state = {
    filters: { search: "", region: "All", product: "All", date_from: "", date_to: "" },
    granularity: "day",
    tablePage: 1,
    currentSection: "dashboard",
};

const charts = {};
let searchDebounce = null;

// ---------------- Utilities ----------------
function qs(params) {
    const clean = {};
    Object.entries(params).forEach(([k, v]) => { if (v !== "" && v != null && v !== "All") clean[k] = v; });
    return new URLSearchParams(clean).toString();
}
function fmtMoney(v) {
    return "$" + Number(v || 0).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}
function fmtInt(v) { return Number(v || 0).toLocaleString(); }
function cssVar(name) { return getComputedStyle(document.documentElement).getPropertyValue(name).trim(); }

function showToast(message, isError) {
    const toast = document.getElementById("toast");
    document.getElementById("toastMsg").textContent = message;
    toast.classList.toggle("error", !!isError);
    toast.classList.add("show");
    clearTimeout(showToast._t);
    showToast._t = setTimeout(() => toast.classList.remove("show"), 3200);
}

async function apiGet(path, params) {
    const query = qs(Object.assign({}, state.filters, params || {}));
    const res = await fetch(path + (query ? "?" + query : ""));
    if (!res.ok) throw new Error("Request failed: " + path);
    return res.json();
}

// ---------------- Theme ----------------
function applyChartTheme() {
    const ink = cssVar("--ink"), muted = cssVar("--muted"), line = cssVar("--line");
    Chart.defaults.color = muted;
    Chart.defaults.borderColor = line;
    Chart.defaults.font.family = "Inter, system-ui, sans-serif";
    Object.values(charts).forEach((c) => c && c.update());
}
function initTheme() {
    const saved = localStorage.getItem("sda-theme") || "light";
    document.documentElement.setAttribute("data-theme", saved);
    updateThemeIcon(saved);
    document.getElementById("themeToggle").addEventListener("click", () => {
        const next = document.documentElement.getAttribute("data-theme") === "dark" ? "light" : "dark";
        document.documentElement.setAttribute("data-theme", next);
        localStorage.setItem("sda-theme", next);
        updateThemeIcon(next);
        applyChartTheme();
    });
}
function updateThemeIcon(theme) {
    document.getElementById("themeToggle").innerHTML = theme === "dark" ? '<i class="bi bi-sun-fill"></i>' : '<i class="bi bi-moon-fill"></i>';
}

// ---------------- Navigation ----------------
const sectionMeta = {
    dashboard: { title: "Main Dashboard", subtitle: "Overview of key sales metrics, performance KPIs, and multi-dimensional visualizations" },
    upload: { title: "Data Upload", subtitle: "Replace the current dataset with your own CSV export" },
    analysis: { title: "Sales Analysis", subtitle: "Product, regional, hourly and distribution breakdowns" },
    profit: { title: "Profit Analysis", subtitle: "Estimated profit by region and product (enhancement module)" },
    forecast: { title: "Sales Forecast", subtitle: "Linear-trend projection of upcoming monthly sales" },
    table: { title: "Sales Records", subtitle: "Cleaned, deduplicated order-level data" },
    about: { title: "About Project", subtitle: "Abstract, methodology, team and tech stack" },
};

function showSection(name) {
    state.currentSection = name;
    document.querySelectorAll(".section").forEach((s) => s.classList.remove("active"));
    document.getElementById("section-" + name).classList.add("active");
    document.querySelectorAll("#navMenu a").forEach((a) => a.classList.toggle("active", a.dataset.section === name));
    document.getElementById("pageTitle").textContent = sectionMeta[name].title;
    document.getElementById("pageSubtitle").textContent = sectionMeta[name].subtitle;
    if (window.innerWidth <= 991) document.getElementById("sidebar").classList.remove("open");
    loadSection(name);
}

function loadSection(name) {
    if (name === "dashboard") { loadKpis(); loadTrend(); }
    else if (name === "analysis") { loadKpis(); loadSalesAnalysis(); }
    else if (name === "profit") { loadKpis(); loadProfit(); }
    else if (name === "forecast") { loadForecast(); }
    else if (name === "table") { state.tablePage = 1; loadTable(); }
}

// ---------------- Filters ----------------
function syncFilterInputs() {
    document.querySelectorAll(".filter-input").forEach((el) => {
        const key = el.dataset.filter;
        if (el.value !== state.filters[key]) el.value = state.filters[key];
    });
}

function populateFilterOptions(meta) {
    document.querySelectorAll('select[data-filter="region"]').forEach((sel) => {
        sel.innerHTML = '<option value="All">All Regions</option>' + meta.regions.map((r) => `<option value="${r}">${r}</option>`).join("");
    });
    document.querySelectorAll('select[data-filter="product"]').forEach((sel) => {
        sel.innerHTML = '<option value="All">All Products</option>' + meta.products.map((p) => `<option value="${p}">${p}</option>`).join("");
    });
    syncFilterInputs();
}

function updateFilterMeta(filteredCount, totalCount) {
    document.querySelectorAll(".filter-record-count").forEach((el) => (el.textContent = filteredCount));
    document.querySelectorAll(".filter-total-count").forEach((el) => (el.textContent = totalCount));
}

function bindFilterEvents() {
    document.querySelectorAll(".filter-input").forEach((el) => {
        const key = el.dataset.filter;
        const handler = () => {
            state.filters[key] = el.value;
            syncFilterInputs();
            if (key === "search") {
                clearTimeout(searchDebounce);
                searchDebounce = setTimeout(() => loadSection(state.currentSection), 350);
            } else {
                loadSection(state.currentSection);
            }
        };
        el.addEventListener(el.tagName === "SELECT" ? "change" : "input", handler);
    });
    document.querySelectorAll(".filter-reset").forEach((btn) => {
        btn.addEventListener("click", () => {
            state.filters = { search: "", region: "All", product: "All", date_from: "", date_to: "" };
            syncFilterInputs();
            loadSection(state.currentSection);
        });
    });
}

// ---------------- Dashboard ----------------
async function loadKpis() {
    try {
        const data = await apiGet("/api/kpis");
        document.getElementById("kpiTotalSales").textContent = fmtMoney(data.total_sales);
        document.getElementById("kpiAverageSales").textContent = fmtMoney(data.average_sales);
        document.getElementById("kpiTotalProfit").textContent = fmtMoney(data.total_profit);
        document.getElementById("kpiMarginPill").textContent = "↗ " + data.profit_margin.toFixed(1) + "% Margin";
        document.getElementById("kpiTotalOrders").textContent = fmtInt(data.total_orders);
        document.getElementById("kpiTotalQuantity").textContent = fmtInt(data.total_quantity);
        document.getElementById("datasetCount").textContent = data.total_count + " Records";
        updateFilterMeta(data.filtered_count, data.total_count);
        const profitTotal = document.getElementById("profitTotal");
        if (profitTotal) { profitTotal.textContent = fmtMoney(data.total_profit); document.getElementById("profitMargin").textContent = data.profit_margin.toFixed(1) + "%"; }
    } catch (e) { console.error(e); }
}

async function loadTrend() {
    try {
        const data = await apiGet("/api/trend", { granularity: state.granularity });
        document.getElementById("periodBadge").textContent = data.labels.length + " Periods";
        const ctx = document.getElementById("trendChart");
        const gradient = ctx.getContext("2d").createLinearGradient(0, 0, 0, 300);
        gradient.addColorStop(0, "rgba(109,92,248,0.25)");
        gradient.addColorStop(1, "rgba(109,92,248,0)");
        if (charts.trend) charts.trend.destroy();
        charts.trend = new Chart(ctx, {
            type: "line",
            data: { labels: data.labels, datasets: [{ label: "Sales Revenue ($)", data: data.values, borderColor: "#6d5cf8", backgroundColor: gradient, fill: true, tension: 0.35, pointRadius: 3, pointBackgroundColor: "#6d5cf8" }] },
            options: {
                responsive: true, maintainAspectRatio: false,
                plugins: { legend: { display: true, position: "top", align: "start", labels: { usePointStyle: true } } },
                scales: { y: { ticks: { callback: (v) => "$" + v.toLocaleString() }, grid: { color: cssVar("--line") } }, x: { grid: { display: false } } },
            },
        });
    } catch (e) { console.error(e); }
}

document.addEventListener("click", (e) => {
    if (e.target.closest("#granularityChips .chip")) {
        const chip = e.target.closest(".chip");
        document.querySelectorAll("#granularityChips .chip").forEach((c) => c.classList.remove("active"));
        chip.classList.add("active");
        state.granularity = chip.dataset.granularity;
        loadTrend();
    }
});

// ---------------- Sales Analysis ----------------
function barChart(canvasId, labels, values, color, horizontal) {
    if (charts[canvasId]) charts[canvasId].destroy();
    charts[canvasId] = new Chart(document.getElementById(canvasId), {
        type: "bar",
        data: { labels, datasets: [{ data: values, backgroundColor: color, borderRadius: 6, maxBarThickness: 34 }] },
        options: {
            indexAxis: horizontal ? "y" : "x",
            responsive: true, maintainAspectRatio: false,
            plugins: { legend: { display: false } },
            scales: { x: { grid: { display: horizontal }, ticks: { autoSkip: true, maxRotation: horizontal ? 0 : 55, minRotation: horizontal ? 0 : 45 } }, y: { grid: { display: !horizontal } } },
        },
    });
}
function lineChart(canvasId, labels, values, color) {
    if (charts[canvasId]) charts[canvasId].destroy();
    charts[canvasId] = new Chart(document.getElementById(canvasId), {
        type: "line",
        data: { labels, datasets: [{ data: values, borderColor: color, backgroundColor: "transparent", tension: 0.35, pointRadius: 2 }] },
        options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } }, scales: { x: { grid: { display: false } } } },
    });
}

async function loadSalesAnalysis() {
    try {
        const data = await apiGet("/api/sales-analysis");
        barChart("productChart", data.product_sales.labels, data.product_sales.values, "#6d5cf8");
        barChart("regionChart", data.region_sales.labels, data.region_sales.values, "#2563eb");
        lineChart("hourlyChart", data.hourly_sales.labels, data.hourly_sales.values, "#16a34a");
        barChart("histogramChart", data.histogram.labels, data.histogram.values, "#ea580c");
        barChart("topProductsChart", data.top_products.labels, data.top_products.values, "#0ea5a4", true);
    } catch (e) { console.error(e); }
}

// ---------------- Profit Analysis ----------------
async function loadProfit() {
    try {
        const data = await apiGet("/api/profit");
        barChart("profitRegionChart", data.profit_by_region.labels, data.profit_by_region.values, "#16a34a");
        barChart("profitProductChart", data.top_profit_products.labels, data.top_profit_products.values, "#0ea5a4", true);
    } catch (e) { console.error(e); }
}

// ---------------- Forecast ----------------
async function loadForecast() {
    try {
        const data = await apiGet("/api/forecast", { periods: 3 });
        const labels = data.actual.labels.concat(data.forecast.labels);
        const actualValues = data.actual.values.concat(Array(data.forecast.labels.length).fill(null));
        const forecastValues = Array(data.actual.labels.length - 1).fill(null).concat(
            data.actual.values.slice(-1), data.forecast.values
        );
        if (charts.forecast) charts.forecast.destroy();
        charts.forecast = new Chart(document.getElementById("forecastChart"), {
            type: "line",
            data: {
                labels,
                datasets: [
                    { label: "Actual", data: actualValues, borderColor: "#2563eb", backgroundColor: "transparent", tension: 0.3, pointRadius: 3 },
                    { label: "Forecast", data: forecastValues, borderColor: "#ea580c", borderDash: [6, 4], backgroundColor: "transparent", tension: 0.3, pointRadius: 3 },
                ],
            },
            options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { position: "top", align: "start" } }, scales: { y: { ticks: { callback: (v) => "$" + v.toLocaleString() } } } },
        });
        const badge = document.getElementById("forecastTrendBadge");
        badge.textContent = data.trend.charAt(0).toUpperCase() + data.trend.slice(1) + " trend";
    } catch (e) { console.error(e); }
}

// ---------------- Data Table ----------------
async function loadTable() {
    try {
        const data = await apiGet("/api/table", { page: state.tablePage, page_size: 20 });
        const tbody = document.getElementById("tableBody");
        if (!data.rows.length) {
            tbody.innerHTML = '<tr><td colspan="8"><div class="empty-state"><i class="bi bi-inbox" style="font-size:26px"></i><p>No records match the selected filters.</p></div></td></tr>';
        } else {
            tbody.innerHTML = data.rows.map((r) => `
                <tr>
                    <td><span class="order-id-chip">${r.order_id}</span></td>
                    <td>${r.product}</td>
                    <td>${r.quantity}</td>
                    <td>${fmtMoney(r.price)}</td>
                    <td>${fmtMoney(r.sales)}</td>
                    <td>${fmtMoney(r.profit)}</td>
                    <td>${r.date}</td>
                    <td><span class="region-chip">${r.region}</span></td>
                </tr>`).join("");
        }
        const totalPages = Math.max(Math.ceil(data.total / data.page_size), 1);
        document.getElementById("tableSummary").textContent = `Showing ${data.rows.length ? (data.page - 1) * data.page_size + 1 : 0}-${(data.page - 1) * data.page_size + data.rows.length} of ${data.total} orders`;
        document.getElementById("pageIndicator").textContent = `Page ${data.page} of ${totalPages}`;
        document.getElementById("prevPageBtn").disabled = data.page <= 1;
        document.getElementById("nextPageBtn").disabled = data.page >= totalPages;
    } catch (e) { console.error(e); }
}
document.getElementById("prevPageBtn")?.addEventListener("click", () => { if (state.tablePage > 1) { state.tablePage--; loadTable(); } });
document.getElementById("nextPageBtn")?.addEventListener("click", () => { state.tablePage++; loadTable(); });

// ---------------- AI Insights ----------------
async function generateInsights() {
    const card = document.querySelector(".insights-card");
    const originalHTML = card.innerHTML;
    card.innerHTML = '<div class="insight-loading"><i class="bi bi-hourglass-split"></i> Analyzing filtered data...</div>';
    try {
        const data = await apiGet("/api/insights");
        card.innerHTML = `
            <div class="tag"><i class="bi bi-stars"></i> AI INSIGHTS</div>
            <ul class="insight-list">${data.insights.map((i) => `<li><i class="bi bi-lightbulb-fill"></i><span>${i}</span></li>`).join("")}</ul>
            <button class="btn-insights mt-2" id="regenerateInsightsBtn"><i class="bi bi-arrow-clockwise"></i> Regenerate</button>`;
        document.getElementById("regenerateInsightsBtn").addEventListener("click", generateInsights);
    } catch (e) {
        card.innerHTML = originalHTML;
        showToast("Could not generate insights.", true);
    }
}

// ---------------- Upload ----------------
function initUpload() {
    const input = document.getElementById("fileInput"), zone = document.getElementById("dropZone");
    const choose = document.getElementById("chooseBtn"), nameEl = document.getElementById("fileName"), submitBtn = document.getElementById("uploadSubmitBtn");
    choose.addEventListener("click", () => input.click());
    function show(file) {
        if (!file) return;
        if (!file.name.toLowerCase().endsWith(".csv")) { showToast("Please select a CSV file.", true); return; }
        nameEl.textContent = "Selected: " + file.name;
        submitBtn.disabled = false;
    }
    input.addEventListener("change", () => show(input.files[0]));
    ["dragenter", "dragover"].forEach((evt) => zone.addEventListener(evt, (e) => { e.preventDefault(); zone.classList.add("dragging"); }));
    ["dragleave", "drop"].forEach((evt) => zone.addEventListener(evt, (e) => { e.preventDefault(); zone.classList.remove("dragging"); }));
    zone.addEventListener("drop", (e) => { input.files = e.dataTransfer.files; show(e.dataTransfer.files[0]); });

    document.getElementById("uploadForm").addEventListener("submit", async (e) => {
        e.preventDefault();
        if (!input.files[0]) return;
        const formData = new FormData();
        formData.append("file", input.files[0]);
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<i class="bi bi-hourglass-split"></i> Analyzing...';
        try {
            const res = await fetch("/api/upload", { method: "POST", body: formData });
            const data = await res.json();
            if (data.success) {
                showToast(data.message);
                await bootstrapMeta();
                showSection("dashboard");
            } else {
                showToast(data.message, true);
            }
        } catch (err) {
            showToast("Upload failed.", true);
        } finally {
            submitBtn.disabled = false;
            submitBtn.innerHTML = '<i class="bi bi-bar-chart-line"></i> Analyze Dataset';
            nameEl.textContent = "";
        }
    });
}

// ---------------- Bootstrap ----------------
async function bootstrapMeta() {
    const meta = await apiGet("/api/meta");
    document.getElementById("datasetName").textContent = meta.dataset_name;
    populateFilterOptions(meta);
    await loadKpis();
    loadSection(state.currentSection);
}

document.addEventListener("DOMContentLoaded", () => {
    initTheme();
    applyChartTheme();
    bindFilterEvents();
    initUpload();

    document.getElementById("navMenu").addEventListener("click", (e) => {
        const link = e.target.closest("a[data-section]");
        if (link) showSection(link.dataset.section);
    });
    document.getElementById("menuBtn").addEventListener("click", () => document.getElementById("sidebar").classList.toggle("open"));
    document.getElementById("generateInsightsBtn").addEventListener("click", generateInsights);
    document.getElementById("topInsightsBtn").addEventListener("click", generateInsights);
    document.getElementById("refreshBtn").addEventListener("click", () => loadSection(state.currentSection));
    document.getElementById("resetDatasetBtn").addEventListener("click", async () => {
        if (!confirm("Restore the bundled sample dataset? This replaces any uploaded data.")) return;
        try {
            await fetch("/api/reset", { method: "POST" });
            showToast("Sample dataset restored.");
            await bootstrapMeta();
        } catch (e) { showToast("Could not reset dataset.", true); }
    });
    const exportHandler = () => { window.location.href = "/api/export?" + qs(state.filters); };
    document.getElementById("exportBtn").addEventListener("click", exportHandler);
    document.getElementById("exportBtn2")?.addEventListener("click", exportHandler);

    bootstrapMeta();
});
