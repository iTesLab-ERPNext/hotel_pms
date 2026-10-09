// Hotel PMS — Main Dashboard
frappe.pages["hotel-pms-dashboard"].on_page_load = function (wrapper) {
	const page = frappe.ui.make_app_page({
		parent: wrapper,
		title: __("Hotel Dashboard"),
		single_column: true,
	});

	page.add_inner_button(__("Refresh"),        () => wrapper._dash.refresh(),                       "fa fa-sync-alt");
	page.add_inner_button(__("New Reservation"), () => frappe.new_doc("Hotel Reservation"),           "fa fa-plus");
	page.add_inner_button(__("Room Board"),      () => frappe.set_route("room-board"),                "fa fa-th-large");
	page.add_inner_button(__("Room Planning"),   () => frappe.set_route("room-planning"),             "fa fa-calendar-alt");

	wrapper._dash = new HotelDashboard(page);
};

frappe.pages["hotel-pms-dashboard"].on_page_show = function (wrapper) {
	if (wrapper._dash) wrapper._dash.refresh();
};

// ─── palette ─────────────────────────────────────────────────────────────────
const C = {
	blue:   "#1f6feb", green:  "#2da44e", red:    "#f85149",
	orange: "#e36209", teal:   "#0db7c0", purple: "#8b5cf6",
	yellow: "#d29922", gray:   "#6e7681", indigo: "#4c6ef5",
	pink:   "#e83e8c",
};
const CHART_COLORS = [C.blue, C.green, C.orange, C.purple, C.teal, C.red, C.yellow, C.indigo, C.pink, C.gray];

// ─── HiDPI canvas factory ────────────────────────────────────────────────────
function makeCanvas(container, w, h) {
	const dpr = window.devicePixelRatio || 1;
	const c   = document.createElement("canvas");
	c.width   = w * dpr; c.height = h * dpr;
	c.style.width = w + "px"; c.style.height = h + "px";
	const ctx = c.getContext("2d");
	ctx.scale(dpr, dpr);
	container.appendChild(c);
	return { canvas: c, ctx, w, h, dpr };
}

// ─── Theme helpers ────────────────────────────────────────────────────────────
function css(prop) {
	return getComputedStyle(document.documentElement).getPropertyValue(prop).trim() || null;
}
function cardBg()    { return css("--card-bg")     || "#ffffff"; }
function textColor() { return css("--text-color")  || "#24292f"; }
function mutedColor(){ return css("--text-muted")  || "#6e7681"; }
function borderCol() { return css("--border-color")|| "#d0d7de"; }

// ─── Tooltip helper ──────────────────────────────────────────────────────────
class CanvasTooltip {
	constructor(canvas) {
		this.el = document.createElement("div");
		Object.assign(this.el.style, {
			position:"absolute", pointerEvents:"none", opacity:"0",
			background:"rgba(36,41,47,.88)", color:"#fff",
			borderRadius:"5px", padding:"5px 9px", fontSize:"12px",
			fontFamily:"var(--font-stack,sans-serif)", lineHeight:"1.5",
			zIndex:"999", transition:"opacity .15s", maxWidth:"180px",
		});
		canvas.parentElement.style.position = "relative";
		canvas.parentElement.appendChild(this.el);
	}
	show(x, y, html) {
		this.el.innerHTML = html;
		this.el.style.left    = (x + 12) + "px";
		this.el.style.top     = (y - 10) + "px";
		this.el.style.opacity = "1";
	}
	hide() { this.el.style.opacity = "0"; }
}

// ─── Chart renderers ─────────────────────────────────────────────────────────
function drawDonut(container, labels, values, colors) {
	container.innerHTML = "";
	const W = container.offsetWidth || 260, H = container.offsetHeight || 220;
	const { canvas, ctx, w, h } = makeCanvas(container, W, H);
	const total = values.reduce((a, b) => a + b, 0);
	const CX = w * 0.42, CY = h * 0.5;
	const R  = Math.min(CX, CY) - 16, r2 = R * 0.55;

	// Slices
	let angle = -Math.PI / 2;
	const slices = [];
	values.forEach((v, i) => {
		const sweep = (v / Math.max(total, 1)) * 2 * Math.PI;
		slices.push({ start: angle, end: angle + sweep, i });
		if (v > 0) {
			ctx.beginPath(); ctx.moveTo(CX, CY);
			ctx.arc(CX, CY, R, angle, angle + sweep);
			ctx.closePath(); ctx.fillStyle = colors[i]; ctx.fill();
		}
		angle += sweep;
	});

	// Hole
	ctx.beginPath(); ctx.arc(CX, CY, r2, 0, 2 * Math.PI);
	ctx.fillStyle = cardBg(); ctx.fill();

	// Centre label
	ctx.fillStyle = textColor();
	ctx.font = `bold ${Math.round(R * 0.3)}px var(--font-stack,sans-serif)`;
	ctx.textAlign = "center"; ctx.textBaseline = "middle";
	ctx.fillText(total, CX, CY - 7);
	ctx.font = `${Math.round(R * 0.18)}px var(--font-stack,sans-serif)`;
	ctx.fillStyle = mutedColor();
	ctx.fillText(__("Total"), CX, CY + 11);

	// Legend (right side)
	const legX = w * 0.84 + 4, legStartY = 18, rowH = 18;
	const nonZero = labels.filter((_, i) => values[i] > 0);
	let li = 0;
	labels.forEach((lbl, i) => {
		if (!values[i]) return;
		const ly = legStartY + li * rowH;
		ctx.fillStyle = colors[i]; ctx.fillRect(legX - w * 0.84 + w * 0.855 - 8, ly, 9, 9);
		ctx.fillStyle = textColor();
		ctx.font = `11px var(--font-stack,sans-serif)`;
		ctx.textAlign = "left"; ctx.textBaseline = "top";
		const pct = Math.round(values[i] / Math.max(total, 1) * 100);
		ctx.fillText(`${lbl.length > 11 ? lbl.slice(0,10)+"…" : lbl}`, legX - w * 0.84 + w * 0.855 + 3, ly);
		ctx.fillStyle = mutedColor();
		ctx.font = `10px var(--font-stack,sans-serif)`;
		ctx.fillText(`${values[i]} (${pct}%)`, legX - w * 0.84 + w * 0.855 + 3, ly + 11);
		li++;
	});

	// Tooltip
	const tip = new CanvasTooltip(canvas);
	canvas.addEventListener("mousemove", e => {
		const rect = canvas.getBoundingClientRect();
		const mx   = e.clientX - rect.left, my = e.clientY - rect.top;
		const dx   = mx - CX, dy = my - CY, dist = Math.sqrt(dx * dx + dy * dy);
		if (dist < r2 || dist > R) { tip.hide(); return; }
		const ang = Math.atan2(dy, dx);
		const a   = (ang < -Math.PI / 2) ? ang + 2 * Math.PI : ang;
		const sl  = slices.find(s => {
			const start = s.start < -Math.PI / 2 ? s.start + 2 * Math.PI : s.start;
			const end   = s.end   < -Math.PI / 2 ? s.end   + 2 * Math.PI : s.end;
			return a >= start && a <= end;
		});
		if (sl && values[sl.i]) {
			const pct = Math.round(values[sl.i] / Math.max(total, 1) * 100);
			tip.show(mx, my, `<b>${labels[sl.i]}</b><br>${values[sl.i]} <span style="color:#aaa">(${pct}%)</span>`);
		} else { tip.hide(); }
	});
	canvas.addEventListener("mouseleave", () => tip.hide());
}

function drawBar(container, labels, values, colors) {
	container.innerHTML = "";
	const W = container.offsetWidth || 300, H = container.offsetHeight || 220;
	const { canvas, ctx, w, h } = makeCanvas(container, W, H);
	const padL = 10, padR = 10, padT = 20, padB = 38;
	const bW   = (w - padL - padR) / Math.max(labels.length, 1);
	const max  = Math.max(...values, 1);

	// Draw bars
	values.forEach((v, i) => {
		const bH = Math.round((v / max) * (h - padT - padB));
		const x  = padL + i * bW + bW * 0.1;
		const y  = h - padB - bH;
		// Rounded top
		const bw2 = bW * 0.8, r = Math.min(4, bw2 / 2, bH);
		ctx.beginPath();
		ctx.moveTo(x + r, y);
		ctx.lineTo(x + bw2 - r, y);
		ctx.quadraticCurveTo(x + bw2, y, x + bw2, y + r);
		ctx.lineTo(x + bw2, y + bH);
		ctx.lineTo(x, y + bH);
		ctx.lineTo(x, y + r);
		ctx.quadraticCurveTo(x, y, x + r, y);
		ctx.closePath();
		ctx.fillStyle = colors[i] || C.blue;
		ctx.fill();

		// Value label on bar
		if (v > 0) {
			ctx.fillStyle = colors[i] || C.blue;
			ctx.font = `bold 11px var(--font-stack,sans-serif)`;
			ctx.textAlign = "center"; ctx.textBaseline = "bottom";
			ctx.fillText(v, x + bw2 / 2, y - 2);
		}

		// X label
		ctx.fillStyle = mutedColor();
		ctx.font = `10px var(--font-stack,sans-serif)`;
		ctx.textAlign = "center"; ctx.textBaseline = "top";
		const lbl = labels[i].length > 9 ? labels[i].slice(0, 8) + "…" : labels[i];
		ctx.fillText(lbl, x + bw2 / 2, h - padB + 5);
	});

	// Tooltip
	const tip = new CanvasTooltip(canvas);
	canvas.addEventListener("mousemove", e => {
		const rect = canvas.getBoundingClientRect();
		const mx   = e.clientX - rect.left;
		const idx  = Math.floor((mx - padL) / bW);
		if (idx >= 0 && idx < values.length && values[idx] !== undefined) {
			tip.show(mx, e.clientY - rect.top, `<b>${labels[idx]}</b><br>${values[idx]}`);
		} else { tip.hide(); }
	});
	canvas.addEventListener("mouseleave", () => tip.hide());
}

function drawLine(container, labels, values, color, showFill) {
	container.innerHTML = "";
	const W = container.offsetWidth || 300, H = container.offsetHeight || 220;
	const { canvas, ctx, w, h } = makeCanvas(container, W, H);
	const padL = 46, padR = 12, padT = 16, padB = 32;
	const n   = labels.length;
	const max = Math.max(...values, 1);
	const min = Math.min(...values, 0);
	const rng = max - min || 1;

	const pts = values.map((v, i) => ({
		x: padL + (i / Math.max(n - 1, 1)) * (w - padL - padR),
		y: padT + (1 - (v - min) / rng) * (h - padT - padB),
		v,
	}));

	// Grid
	[0, 0.25, 0.5, 0.75, 1].forEach(pct => {
		const y   = padT + pct * (h - padT - padB);
		const val = Math.round(max - pct * rng);
		ctx.strokeStyle = borderCol(); ctx.lineWidth = 0.6;
		ctx.setLineDash([3, 3]);
		ctx.beginPath(); ctx.moveTo(padL, y); ctx.lineTo(w - padR, y); ctx.stroke();
		ctx.setLineDash([]);
		ctx.fillStyle = mutedColor();
		ctx.font = "9px var(--font-stack,sans-serif)";
		ctx.textAlign = "right"; ctx.textBaseline = "middle";
		ctx.fillText(val.toLocaleString(), padL - 5, y);
	});

	// Gradient fill
	if (showFill !== false && pts.length > 1) {
		const grad = ctx.createLinearGradient(0, padT, 0, h - padB);
		grad.addColorStop(0, (color || C.teal) + "55");
		grad.addColorStop(1, (color || C.teal) + "00");
		ctx.beginPath();
		pts.forEach((p, i) => i === 0 ? ctx.moveTo(p.x, p.y) : ctx.lineTo(p.x, p.y));
		ctx.lineTo(pts[pts.length - 1].x, h - padB);
		ctx.lineTo(pts[0].x, h - padB);
		ctx.closePath();
		ctx.fillStyle = grad; ctx.fill();
	}

	// Line
	if (pts.length > 1) {
		ctx.beginPath();
		pts.forEach((p, i) => i === 0 ? ctx.moveTo(p.x, p.y) : ctx.lineTo(p.x, p.y));
		ctx.strokeStyle = color || C.teal; ctx.lineWidth = 2.2;
		ctx.lineJoin = "round"; ctx.stroke();
	}

	// Dots + x labels
	const step = Math.ceil(n / 7);
	pts.forEach((p, i) => {
		ctx.beginPath(); ctx.arc(p.x, p.y, 3, 0, 2 * Math.PI);
		ctx.fillStyle = color || C.teal; ctx.fill();
		ctx.strokeStyle = cardBg(); ctx.lineWidth = 1.5; ctx.stroke();

		if (i % step === 0 || i === n - 1) {
			ctx.fillStyle = mutedColor();
			ctx.font = "9px var(--font-stack,sans-serif)";
			ctx.textAlign = "center"; ctx.textBaseline = "top";
			ctx.fillText(labels[i].slice(5), p.x, h - padB + 5); // "MM-DD"
		}
	});

	// Tooltip
	const tip = new CanvasTooltip(canvas);
	canvas.addEventListener("mousemove", e => {
		const rect = canvas.getBoundingClientRect();
		const mx   = e.clientX - rect.left;
		if (n < 2) return;
		const step2 = (w - padL - padR) / Math.max(n - 1, 1);
		const idx   = Math.round((mx - padL) / step2);
		if (idx >= 0 && idx < n) {
			tip.show(mx, pts[idx].y, `<b>${labels[idx].slice(5)}</b><br>${pts[idx].v.toLocaleString()}`);
		} else { tip.hide(); }
	});
	canvas.addEventListener("mouseleave", () => tip.hide());
}

// ─── Dashboard class ──────────────────────────────────────────────────────────
class HotelDashboard {
	constructor(page) {
		this.page    = page;
		this.wrapper = $(page.body);
		this._build_skeleton();
		this.refresh();
	}

	_build_skeleton() {
		this.wrapper.html(`
<div class="hotel-dash" style="padding:20px 24px;">

  <!-- today strip -->
  <div class="hd-section-label">${__("Today's Operations")}</div>
  <div class="row hd-row" id="hd-today"></div>

  <!-- room status -->
  <div class="hd-section-label mt-4">${__("Room Status")}</div>
  <div class="row hd-row" id="hd-rooms"></div>

  <!-- reservations -->
  <div class="hd-section-label mt-4">${__("Reservations")}</div>
  <div class="row hd-row" id="hd-reservations"></div>

  <!-- financials -->
  <div class="hd-section-label mt-4">${__("Financial")}</div>
  <div class="row hd-row" id="hd-financial"></div>

  <!-- ── Analytics (2 × 2 chart grid) ────────────────────────────────── -->
  <div class="hd-section-label mt-4">${__("Analytics")}</div>
  <div class="row hd-row" id="hd-charts">

    <!-- Row 1 -->
    <div class="col-lg-6 col-12 hd-chart-col">
      <div class="hd-chart-card">
        <div class="hd-chart-header">
          <span class="hd-chart-title">${__("Room Status Distribution")}</span>
          <span class="hd-chart-sub">${__("Current")}</span>
        </div>
        <div id="hd-chart-rooms" class="hd-chart-area"></div>
      </div>
    </div>
    <div class="col-lg-6 col-12 hd-chart-col">
      <div class="hd-chart-card">
        <div class="hd-chart-header">
          <span class="hd-chart-title">${__("Revenue by Charge Type")}</span>
          <span class="hd-chart-sub">${__("This Month")}</span>
        </div>
        <div id="hd-chart-revtype" class="hd-chart-area"></div>
      </div>
    </div>

    <!-- Row 2 -->
    <div class="col-lg-6 col-12 hd-chart-col">
      <div class="hd-chart-card">
        <div class="hd-chart-header">
          <span class="hd-chart-title">${__("Occupancy Rate")}</span>
          <span class="hd-chart-sub">${__("Last 14 Days")}</span>
        </div>
        <div id="hd-chart-occ" class="hd-chart-area"></div>
      </div>
    </div>
    <div class="col-lg-6 col-12 hd-chart-col">
      <div class="hd-chart-card">
        <div class="hd-chart-header">
          <span class="hd-chart-title">${__("Daily Revenue")}</span>
          <span class="hd-chart-sub">${__("Last 14 Days")}</span>
        </div>
        <div id="hd-chart-rev" class="hd-chart-area"></div>
      </div>
    </div>
  </div>

  <!-- quick actions -->
  <div class="hd-section-label mt-4">${__("Quick Actions")}</div>
  <div class="row hd-row" id="hd-actions"></div>

</div>

<style>
.hotel-dash { font-family: var(--font-stack); }
.hd-section-label {
  font-size: 11px; font-weight: 600; letter-spacing: .8px;
  text-transform: uppercase; color: var(--text-muted); margin-bottom: 10px;
}
.hd-row { margin-left: -6px; margin-right: -6px; }
.hd-row > [class*="col-"] { padding: 0 6px 12px; }

/* KPI cards */
.hd-card {
  background: var(--card-bg); border-radius: 8px;
  border: 1px solid var(--border-color); border-left-width: 4px;
  padding: 14px 16px; height: 100%; transition: box-shadow .15s;
}
.hd-card:hover { box-shadow: 0 2px 12px rgba(0,0,0,.08); }
.hd-card.clickable { cursor: pointer; }
.hd-card-val { font-size: 26px; font-weight: 700; line-height: 1; margin-bottom: 3px; }
.hd-card-lbl { font-size: 11px; color: var(--text-muted); font-weight: 500; }
.hd-card-icon { font-size: 30px; opacity: .18; line-height: 1; }

/* Chart cards */
.hd-chart-col { padding: 0 6px 12px; }
.hd-chart-card {
  background: var(--card-bg); border: 1px solid var(--border-color);
  border-radius: 8px; padding: 14px 16px; height: 100%;
}
.hd-chart-header {
  display: flex; justify-content: space-between; align-items: baseline;
  margin-bottom: 12px;
}
.hd-chart-title {
  font-size: 12px; font-weight: 600; color: var(--text-color);
}
.hd-chart-sub {
  font-size: 10px; color: var(--text-muted); text-transform: uppercase;
  letter-spacing: .5px;
}
.hd-chart-area { height: 200px; position: relative; }

/* Action buttons */
.hd-action-btn {
  width: 100%; border-radius: 6px; padding: 10px 8px; font-size: 12px;
  font-weight: 500; border: 1px solid var(--border-color);
  background: var(--card-bg); color: var(--text-color); cursor: pointer;
  transition: background .15s, box-shadow .15s;
  display: flex; flex-direction: column; align-items: center; gap: 5px;
}
.hd-action-btn:hover { background: var(--fg-hover-color); box-shadow: 0 1px 6px rgba(0,0,0,.08); }
.hd-action-btn i { font-size: 18px; }
.col-xl-1-5 { width: 12.5%; }
</style>
`);
	}

	refresh() {
		this.wrapper.find(".hd-card-val").css("opacity", ".4");
		frappe.call({
			method: "hotel_pms.hotel.api.get_dashboard_data",
			callback: r => r.message && this._render(r.message),
		});
	}

	_render(d) {
		this._today(d.today);
		this._rooms(d.rooms);
		this._reservations(d.reservations);
		this._financial(d.financial);
		this._charts(d);
		this._actions();
	}

	// ── stat card helper ─────────────────────────────────────────────────────
	_card({ label, value, color, icon, route, cols = "col-xl-2 col-lg-3 col-sm-4 col-6" }) {
		const c    = C[color] || C.gray;
		const click = route ? "clickable" : "";
		const html  = `
<div class="${cols} hd-col">
  <div class="hd-card ${click}" style="border-left-color:${c};"
       data-route='${JSON.stringify(route || null)}'>
    <div class="d-flex justify-content-between align-items-start">
      <div>
        <div class="hd-card-val" style="color:${c};">${value}</div>
        <div class="hd-card-lbl">${label}</div>
      </div>
      <i class="${icon} hd-card-icon" style="color:${c};"></i>
    </div>
  </div>
</div>`;
		return { html, route };
	}

	_inject(selector, cards) {
		const html = cards.map(c => c.html).join("");
		const $row = this.wrapper.find(selector).html(html);
		$row.find(".clickable").each(function () {
			const route = JSON.parse($(this).attr("data-route") || "null");
			if (route) $(this).on("click", () => frappe.set_route(...route));
		});
	}

	// ── sections ─────────────────────────────────────────────────────────────
	_today(t = {}) {
		const cards = [
			this._card({ label: __("Arrivals Today"),   value: t.arrivals       || 0, color: "blue",   icon: "fa fa-plane-arrival",  route: ["List","Hotel Reservation",{arrival_date:frappe.datetime.get_today(),status:["in",["Confirmed","Checked In"]]}] }),
			this._card({ label: __("Departures Today"), value: t.departures     || 0, color: "orange", icon: "fa fa-plane-departure", route: ["List","Hotel Reservation",{departure_date:frappe.datetime.get_today(),status:"Checked In"}] }),
			this._card({ label: __("Active Stays"),     value: t.active_stays   || 0, color: "green",  icon: "fa fa-bed",             route: ["List","Hotel Stay",{status:"Active"}] }),
			this._card({ label: __("Available Rooms"),  value: t.available_rooms|| 0, color: "teal",   icon: "fa fa-door-open",       route: ["List","Hotel Room",{status:"Available"}] }),
		];
		this._inject("#hd-today", cards);
	}

	_rooms(r = {}) {
		const cards = [
			this._card({ label: __("Total"),       value: r.total       || 0, color: "gray",   icon: "fa fa-building" }),
			this._card({ label: __("Available"),   value: r.available   || 0, color: "green",  icon: "fa fa-check-circle",  route: ["List","Hotel Room",{status:"Available"}] }),
			this._card({ label: __("Occupied"),    value: r.occupied    || 0, color: "blue",   icon: "fa fa-user",          route: ["List","Hotel Room",{status:"Occupied"}] }),
			this._card({ label: __("Reserved"),    value: r.reserved    || 0, color: "purple", icon: "fa fa-bookmark",      route: ["List","Hotel Room",{status:"Reserved"}] }),
			this._card({ label: __("Cleaning"),    value: r.cleaning    || 0, color: "yellow", icon: "fa fa-broom",         route: ["List","Hotel Room",{status:"Cleaning"}] }),
			this._card({ label: __("Maintenance"), value: r.maintenance || 0, color: "red",    icon: "fa fa-tools",         route: ["List","Hotel Room",{status:"Maintenance"}] }),
		];
		this._inject("#hd-rooms", cards);
	}

	_reservations(res = {}) {
		const cards = [
			this._card({ label: __("Draft"),      value: res.draft      || 0, color: "gray",   icon: "fa fa-file",           route: ["List","Hotel Reservation",{status:"Draft"}] }),
			this._card({ label: __("Confirmed"),  value: res.confirmed  || 0, color: "blue",   icon: "fa fa-check",          route: ["List","Hotel Reservation",{status:"Confirmed"}] }),
			this._card({ label: __("Checked In"), value: res.checked_in || 0, color: "green",  icon: "fa fa-sign-in-alt",    route: ["List","Hotel Reservation",{status:"Checked In"}] }),
			this._card({ label: __("Completed"),  value: res.completed  || 0, color: "teal",   icon: "fa fa-flag-checkered", route: ["List","Hotel Reservation",{status:"Completed"}] }),
			this._card({ label: __("Cancelled"),  value: res.cancelled  || 0, color: "red",    icon: "fa fa-times-circle",   route: ["List","Hotel Reservation",{status:"Cancelled"}] }),
			this._card({ label: __("No Show"),    value: res.no_show    || 0, color: "orange", icon: "fa fa-ghost",          route: ["List","Hotel Reservation",{status:"No Show"}] }),
		];
		this._inject("#hd-reservations", cards);
	}

	_financial(fin = {}) {
		const fmt  = v => format_currency(v || 0);
		const cards = [
			this._card({ label: __("Today's Collections"), value: fmt(fin.today_payments),       color: "green",  icon: "fa fa-cash-register",        cols: "col-xl-3 col-md-6 col-12" }),
			this._card({ label: __("Outstanding Balance"), value: fmt(fin.outstanding_balances), color: (fin.outstanding_balances || 0) > 0 ? "red" : "gray", icon: "fa fa-exclamation-circle", cols: "col-xl-3 col-md-6 col-12" }),
			this._card({ label: __("Open Folios"),         value: fin.open_folios || 0,          color: "blue",   icon: "fa fa-file-invoice",          cols: "col-xl-3 col-md-6 col-12", route: ["List","Hotel Folio",{status:["in",["Open","Partially Paid"]]}] }),
			this._card({ label: __("Payments This Month"), value: fmt(fin.month_payments),       color: "teal",   icon: "fa fa-coins",                 cols: "col-xl-3 col-md-6 col-12" }),
		];
		this._inject("#hd-financial", cards);
	}

	// ── charts ────────────────────────────────────────────────────────────────
	_charts(d) {
		// Chart 1 — Room Status donut
		const rm = d.rooms || {};
		drawDonut(
			this.wrapper.find("#hd-chart-rooms")[0],
			[__("Available"), __("Occupied"), __("Reserved"), __("Cleaning"), __("Maintenance"), __("Out of Service")],
			[rm.available||0, rm.occupied||0, rm.reserved||0, rm.cleaning||0, rm.maintenance||0, rm.out_of_service||0],
			[C.green, C.blue, C.purple, C.yellow, C.red, C.gray]
		);

		// Chart 2 — Revenue by Charge Type (donut)
		frappe.call({
			method: "hotel_pms.hotel.api.get_revenue_by_type",
			callback: r => {
				if (!r.message) return;
				const el = this.wrapper.find("#hd-chart-revtype")[0];
				if (!el) return;
				const { labels, values } = r.message;
				if (!labels.length) {
					el.innerHTML = `<div style="text-align:center;padding:60px 0;color:var(--text-muted);font-size:13px;">${__("No data this month")}</div>`;
					return;
				}
				drawDonut(el, labels, values, CHART_COLORS);
			},
		});

		// Chart 3 — Occupancy % trend (line)
		frappe.call({
			method: "hotel_pms.hotel.api.get_occupancy_trend",
			callback: r => {
				if (!r.message) return;
				const el = this.wrapper.find("#hd-chart-occ")[0];
				if (!el) return;
				drawLine(el, r.message.labels, r.message.values, C.indigo, true);
			},
		});

		// Chart 4 — Daily revenue trend (line)
		frappe.call({
			method: "hotel_pms.hotel.api.get_revenue_trend",
			callback: r => {
				if (!r.message) return;
				const el = this.wrapper.find("#hd-chart-rev")[0];
				if (!el) return;
				drawLine(el, r.message.labels, r.message.values, C.teal, true);
			},
		});
	}

	// ── quick actions ─────────────────────────────────────────────────────────
	_actions() {
		const actions = [
			{ label: __("New Reservation"), icon: "fa fa-plus-circle",        fn: () => frappe.new_doc("Hotel Reservation") },
			{ label: __("New Customer"),    icon: "fa fa-user-plus",           fn: () => frappe.new_doc("Hotel Customer") },
			{ label: __("Room Planning"),   icon: "fa fa-calendar-alt",        fn: () => frappe.set_route("room-planning") },
			{ label: __("Calendar"),        icon: "fa fa-calendar",            fn: () => frappe.set_route("List","Hotel Reservation","Calendar") },
			{ label: __("Housekeeping"),    icon: "fa fa-broom",               fn: () => frappe.set_route("List","Hotel Housekeeping") },
			{ label: __("Payments"),        icon: "fa fa-money-bill-wave",     fn: () => frappe.set_route("List","Hotel Payment") },
			{ label: __("Folios"),          icon: "fa fa-file-invoice-dollar", fn: () => frappe.set_route("List","Hotel Folio") },
			{ label: __("Reports"),         icon: "fa fa-chart-bar",           fn: () => frappe.set_route("query-report","Daily Room Occupancy") },
		];

		const html = actions.map((a, i) => `
<div class="col-xl-1-5 col-lg-2 col-md-3 col-4 mb-2">
  <button class="hd-action-btn" data-idx="${i}">
    <i class="${a.icon}"></i>
    <span>${a.label}</span>
  </button>
</div>`).join("");

		const $row = this.wrapper.find("#hd-actions").html(`<style>.col-xl-1-5{width:12.5%;}</style>${html}`);
		$row.find(".hd-action-btn").each(function () {
			const idx = parseInt($(this).attr("data-idx"));
			$(this).on("click", actions[idx].fn);
		});
	}
}
