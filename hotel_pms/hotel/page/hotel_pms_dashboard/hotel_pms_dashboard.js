// Hotel PMS — Main Dashboard
frappe.pages["hotel-pms-dashboard"].on_page_load = function (wrapper) {
	const page = frappe.ui.make_app_page({
		parent: wrapper,
		title: __("Hotel Dashboard"),
		single_column: true,
	});

	page.add_inner_button(__("Refresh"), () => wrapper._dash.refresh(), "fa fa-refresh");
	page.add_inner_button(__("New Reservation"), () => frappe.new_doc("Hotel Reservation"), "fa fa-plus");
	page.add_inner_button(__("Room Board"), () => frappe.set_route("room-board"), "fa fa-th-large");
	page.add_inner_button(__("Room Planning"), () => frappe.set_route("room-planning"), "fa fa-calendar");

	wrapper._dash = new HotelDashboard(page);
};

frappe.pages["hotel-pms-dashboard"].on_page_show = function (wrapper) {
	if (wrapper._dash) wrapper._dash.refresh();
};

// ─── colour palette ───────────────────────────────────────────────────────────
const C = {
	blue:   "#1f6feb",
	green:  "#2da44e",
	red:    "#f85149",
	orange: "#e36209",
	teal:   "#2ea8a8",
	purple: "#8b5cf6",
	yellow: "#d29922",
	gray:   "#6e7681",
};

class HotelDashboard {
	constructor(page) {
		this.page = page;
		this.wrapper = $(page.body);
		this._build_skeleton();
		this.refresh();
	}

	_build_skeleton() {
		this.wrapper.html(`
<div class="hotel-dash" style="padding:20px 24px;">

  <!-- ── today strip ───────────────────────────────────── -->
  <div class="hd-section-label">${__("Today's Operations")}</div>
  <div class="row hd-row" id="hd-today"></div>

  <!-- ── room status ───────────────────────────────────── -->
  <div class="hd-section-label mt-4">${__("Room Status")}</div>
  <div class="row hd-row" id="hd-rooms"></div>

  <!-- ── reservations ──────────────────────────────────── -->
  <div class="hd-section-label mt-4">${__("Reservations")}</div>
  <div class="row hd-row" id="hd-reservations"></div>

  <!-- ── financials ────────────────────────────────────── -->
  <div class="hd-section-label mt-4">${__("Financial")}</div>
  <div class="row hd-row" id="hd-financial"></div>

  <!-- ── quick actions ─────────────────────────────────── -->
  <div class="hd-section-label mt-4">${__("Quick Actions")}</div>
  <div class="row hd-row" id="hd-actions"></div>

</div>

<style>
.hotel-dash { font-family: var(--font-stack); }
.hd-section-label {
  font-size: 11px;
  font-weight: 600;
  letter-spacing: .8px;
  text-transform: uppercase;
  color: var(--text-muted);
  margin-bottom: 10px;
}
.hd-row { margin-left: -6px; margin-right: -6px; }
.hd-row > [class*="col-"] { padding: 0 6px 12px; }
.hd-card {
  background: var(--card-bg);
  border-radius: 8px;
  border: 1px solid var(--border-color);
  border-left-width: 4px;
  padding: 14px 16px;
  height: 100%;
  transition: box-shadow .15s;
}
.hd-card:hover { box-shadow: 0 2px 12px rgba(0,0,0,.08); }
.hd-card.clickable { cursor: pointer; }
.hd-card-val {
  font-size: 26px;
  font-weight: 700;
  line-height: 1;
  margin-bottom: 3px;
}
.hd-card-lbl {
  font-size: 11px;
  color: var(--text-muted);
  font-weight: 500;
}
.hd-card-icon {
  font-size: 30px;
  opacity: .18;
  line-height: 1;
}
.hd-action-btn {
  width: 100%;
  border-radius: 6px;
  padding: 10px 8px;
  font-size: 12px;
  font-weight: 500;
  border: 1px solid var(--border-color);
  background: var(--card-bg);
  color: var(--text-color);
  cursor: pointer;
  transition: background .15s, box-shadow .15s;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 5px;
}
.hd-action-btn:hover {
  background: var(--fg-hover-color);
  box-shadow: 0 1px 6px rgba(0,0,0,.08);
}
.hd-action-btn i { font-size: 18px; }
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
		this._actions();
	}

	// ── stat card helper ───────────────────────────────────────────────────────
	_card({ label, value, color, icon, route, cols = "col-xl-2 col-lg-3 col-sm-4 col-6" }) {
		const c = C[color] || C.gray;
		const click = route ? "clickable" : "";
		const html = `
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

	// ── sections ───────────────────────────────────────────────────────────────
	_today(t = {}) {
		const cards = [
			this._card({ label: __("Arrivals Today"),  value: t.arrivals      || 0, color: "blue",   icon: "fa fa-plane-arrival",   route: ["List","Hotel Reservation",{arrival_date:frappe.datetime.get_today(),status:["in",["Confirmed","Checked In"]]}] }),
			this._card({ label: __("Departures Today"), value: t.departures    || 0, color: "orange", icon: "fa fa-plane-departure",  route: ["List","Hotel Reservation",{departure_date:frappe.datetime.get_today(),status:"Checked In"}] }),
			this._card({ label: __("Active Stays"),    value: t.active_stays  || 0, color: "green",  icon: "fa fa-bed",             route: ["List","Hotel Stay",{status:"Active"}] }),
			this._card({ label: __("Available Rooms"), value: t.available_rooms|| 0, color: "teal",   icon: "fa fa-door-open",       route: ["List","Hotel Room",{status:"Available"}] }),
		];
		this._inject("#hd-today", cards);
	}

	_rooms(r = {}) {
		const cards = [
			this._card({ label: __("Total"),       value: r.total       || 0, color: "gray",   icon: "fa fa-building" }),
			this._card({ label: __("Available"),   value: r.available   || 0, color: "green",  icon: "fa fa-check-circle",  route: ["List","Hotel Room",{status:"Available"}] }),
			this._card({ label: __("Occupied"),    value: r.occupied    || 0, color: "blue",   icon: "fa fa-user",           route: ["List","Hotel Room",{status:"Occupied"}] }),
			this._card({ label: __("Reserved"),    value: r.reserved    || 0, color: "purple", icon: "fa fa-bookmark",       route: ["List","Hotel Room",{status:"Reserved"}] }),
			this._card({ label: __("Cleaning"),    value: r.cleaning    || 0, color: "yellow", icon: "fa fa-broom",          route: ["List","Hotel Room",{status:"Cleaning"}] }),
			this._card({ label: __("Maintenance"), value: r.maintenance || 0, color: "red",    icon: "fa fa-tools",          route: ["List","Hotel Room",{status:"Maintenance"}] }),
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
		const fmt = v => format_currency(v || 0);
		const cards = [
			this._card({ label: __("Today's Collections"),  value: fmt(fin.today_payments),       color: "green",  icon: "fa fa-cash-register",        cols: "col-xl-3 col-md-6 col-12" }),
			this._card({ label: __("Outstanding Balance"),  value: fmt(fin.outstanding_balances), color: (fin.outstanding_balances || 0) > 0 ? "red" : "gray", icon: "fa fa-exclamation-circle", cols: "col-xl-3 col-md-6 col-12" }),
			this._card({ label: __("Open Folios"),          value: fin.open_folios       || 0,    color: "blue",   icon: "fa fa-file-invoice",          cols: "col-xl-3 col-md-6 col-12", route: ["List","Hotel Folio",{status:["in",["Open","Partially Paid"]]}] }),
			this._card({ label: __("Payments This Month"),  value: fmt(fin.month_payments),       color: "teal",   icon: "fa fa-coins",                 cols: "col-xl-3 col-md-6 col-12" }),
		];
		this._inject("#hd-financial", cards);
	}

	_actions() {
		const actions = [
			{ label: __("New Reservation"), icon: "fa fa-plus-circle",       fn: () => frappe.new_doc("Hotel Reservation") },
			{ label: __("New Customer"),    icon: "fa fa-user-plus",          fn: () => frappe.new_doc("Hotel Customer") },
			{ label: __("Room Planning"),   icon: "fa fa-calendar-alt",       fn: () => frappe.set_route("room-planning") },
			{ label: __("Calendar"),        icon: "fa fa-calendar",           fn: () => frappe.set_route("List","Hotel Reservation","Calendar") },
			{ label: __("Housekeeping"),    icon: "fa fa-broom",              fn: () => frappe.set_route("List","Hotel Housekeeping") },
			{ label: __("Payments"),        icon: "fa fa-money-bill-wave",    fn: () => frappe.set_route("List","Hotel Payment") },
			{ label: __("Folios"),          icon: "fa fa-file-invoice-dollar",fn: () => frappe.set_route("List","Hotel Folio") },
			{ label: __("Reports"),         icon: "fa fa-chart-bar",          fn: () => frappe.set_route("query-report","Daily Room Occupancy") },
		];

		const html = actions.map((a, i) => `
<div class="col-xl-1-5 col-lg-2 col-md-3 col-4 mb-2">
  <button class="hd-action-btn" data-idx="${i}">
    <i class="${a.icon}"></i>
    <span>${a.label}</span>
  </button>
</div>`).join("");

		const $row = this.wrapper.find("#hd-actions").html(`
<style>.col-xl-1-5{width:12.5%;}</style>
${html}`);

		$row.find(".hd-action-btn").each(function () {
			const idx = parseInt($(this).attr("data-idx"));
			$(this).on("click", actions[idx].fn);
		});
	}
}
