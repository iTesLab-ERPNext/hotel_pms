// Hotel PMS — Room Board
frappe.pages["room-board"].on_page_load = function (wrapper) {
	const page = frappe.ui.make_app_page({
		parent: wrapper,
		title: __("Room Board"),
		single_column: true,
	});

	page.set_secondary_action(__("Refresh"), () => wrapper._rb.refresh(), "fa fa-sync-alt");
	page.add_inner_button(__("New Reservation"), () => frappe.new_doc("Hotel Reservation"), "fa fa-plus");
	page.add_inner_button(__("Dashboard"), () => frappe.set_route("hotel-pms-dashboard"), "fa fa-tachometer-alt");

	wrapper._rb = new RoomBoard(page, wrapper);
};

frappe.pages["room-board"].on_page_show = function (wrapper) {
	if (wrapper._rb) wrapper._rb.refresh();
};

// ── colour map ─────────────────────────────────────────────────────────────────
const STATUS_COLOR = {
	"Available":     { border: "#2da44e", badge: "#2da44e", label: "Vacant" },
	"Reserved":      { border: "#1f6feb", badge: "#1f6feb", label: "Reserved" },
	"Occupied":      { border: "#e36209", badge: "#e36209", label: "Occupied" },
	"Maintenance":   { border: "#f85149", badge: "#f85149", label: "Maintenance" },
	"Cleaning":      { border: "#8b5cf6", badge: "#8b5cf6", label: "Cleaning" },
	"Dirty":         { border: "#d29922", badge: "#d29922", label: "Dirty" },
	"Out of Service":{ border: "#6e7681", badge: "#6e7681", label: "Out of Service" },
};
const HK_DOT = {
	"Clean":     "#2da44e",
	"Dirty":     "#d29922",
	"Cleaning":  "#8b5cf6",
	"Inspected": "#1f6feb",
};

class RoomBoard {
	constructor(page, wrapper) {
		this.page    = page;
		this.wrapper = $(wrapper);
		this.filters = { status: "All", hk: "All", type: "All", floor: "All", q: "" };
		this._all_rooms = [];
		this._build();
		this.refresh();
	}

	// ── skeleton ───────────────────────────────────────────────────────────────
	_build() {
		this.wrapper.find(".page-content").html(`
<div class="rb-wrap" style="padding:16px 20px;">

  <!-- filters -->
  <div class="rb-filters d-flex flex-wrap align-items-center mb-3" style="gap:10px;">
    <div>
      <label class="rb-lbl">${__("Status")}</label>
      <select id="rb-f-status" class="rb-sel form-control form-control-sm">
        <option value="All">${__("All")}</option>
        <option value="Available">${__("Available")}</option>
        <option value="Reserved">${__("Reserved")}</option>
        <option value="Occupied">${__("Occupied")}</option>
        <option value="Cleaning">${__("Cleaning")}</option>
        <option value="Maintenance">${__("Maintenance")}</option>
        <option value="Out of Service">${__("Out of Service")}</option>
      </select>
    </div>
    <div>
      <label class="rb-lbl">${__("Housekeeping")}</label>
      <select id="rb-f-hk" class="rb-sel form-control form-control-sm">
        <option value="All">${__("All")}</option>
        <option value="Clean">${__("Clean")}</option>
        <option value="Dirty">${__("Dirty")}</option>
        <option value="Cleaning">${__("Cleaning")}</option>
        <option value="Inspected">${__("Inspected")}</option>
      </select>
    </div>
    <div>
      <label class="rb-lbl">${__("Room Type")}</label>
      <select id="rb-f-type" class="rb-sel form-control form-control-sm">
        <option value="All">${__("All")}</option>
      </select>
    </div>
    <div>
      <label class="rb-lbl">${__("Floor")}</label>
      <select id="rb-f-floor" class="rb-sel form-control form-control-sm">
        <option value="All">${__("All")}</option>
      </select>
    </div>
    <div style="flex:1; min-width:180px;">
      <label class="rb-lbl">${__("Search")}</label>
      <input id="rb-f-q" type="text" class="form-control form-control-sm" placeholder="${__("Room number or guest name")}">
    </div>
  </div>

  <!-- summary bar -->
  <div class="rb-summary d-flex flex-wrap mb-3" id="rb-summary" style="gap:10px;"></div>

  <!-- legend -->
  <div class="rb-legend d-flex flex-wrap mb-3" style="gap:14px; font-size:12px; color:var(--text-muted);">
    <span><span class="rb-dot" style="background:#2da44e;"></span>${__("Vacant")}</span>
    <span><span class="rb-dot" style="background:#1f6feb;"></span>${__("Reserved")}</span>
    <span><span class="rb-dot" style="background:#e36209;"></span>${__("Occupied")}</span>
    <span><span class="rb-dot" style="background:#f85149;"></span>${__("Maintenance")}</span>
    <span><span class="rb-dot" style="background:#8b5cf6;"></span>${__("Cleaning")}</span>
    <span><span class="rb-dot" style="background:#6e7681;"></span>${__("Out of Service")}</span>
  </div>

  <!-- grid -->
  <div id="rb-grid" class="rb-grid"></div>

</div>

<style>
.rb-lbl { font-size:10px; font-weight:600; color:var(--text-muted); text-transform:uppercase; letter-spacing:.5px; display:block; margin-bottom:2px; }
.rb-sel { min-width:120px; }
.rb-summary-tile { background:var(--card-bg); border:1px solid var(--border-color); border-radius:6px; padding:8px 16px; display:flex; flex-direction:column; align-items:center; min-width:90px; }
.rb-summary-tile .val { font-size:22px; font-weight:700; line-height:1; }
.rb-summary-tile .lbl { font-size:10px; color:var(--text-muted); text-transform:uppercase; letter-spacing:.5px; }
.rb-grid { display:grid; grid-template-columns:repeat(auto-fill,minmax(220px,1fr)); gap:12px; }
.rb-card { background:var(--card-bg); border:1px solid var(--border-color); border-top-width:4px; border-radius:8px; padding:14px; cursor:pointer; transition:box-shadow .15s; }
.rb-card:hover { box-shadow:0 2px 12px rgba(0,0,0,.1); }
.rb-card-head { display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:8px; }
.rb-room-num { font-size:16px; font-weight:700; }
.rb-room-type { font-size:10px; color:var(--text-muted); }
.rb-badge { font-size:10px; font-weight:600; border-radius:4px; padding:2px 8px; color:#fff; }
.rb-row { display:flex; justify-content:space-between; font-size:11px; margin-bottom:4px; }
.rb-row-lbl { color:var(--text-muted); }
.rb-row-val { font-weight:500; }
.rb-actions { margin-top:10px; display:flex; gap:6px; }
.rb-btn { font-size:11px; padding:4px 10px; border-radius:4px; border:1px solid var(--border-color); background:var(--card-bg); cursor:pointer; color:var(--text-color); }
.rb-btn:hover { background:var(--fg-hover-color); }
.rb-btn-primary { background:var(--primary); color:#fff; border-color:var(--primary); }
.rb-btn-primary:hover { opacity:.9; }
.rb-dot { display:inline-block; width:9px; height:9px; border-radius:50%; margin-right:4px; }
.rb-hk-dot { display:inline-block; width:7px; height:7px; border-radius:50%; margin-right:3px; }
</style>`);

		// wire filters
		const $w = this.wrapper;
		$w.find("#rb-f-status").on("change", e => { this.filters.status = e.target.value; this._render(); });
		$w.find("#rb-f-hk").on("change",     e => { this.filters.hk     = e.target.value; this._render(); });
		$w.find("#rb-f-type").on("change",   e => { this.filters.type   = e.target.value; this._render(); });
		$w.find("#rb-f-floor").on("change",  e => { this.filters.floor  = e.target.value; this._render(); });
		$w.find("#rb-f-q").on("input",       e => { this.filters.q      = e.target.value.toLowerCase(); this._render(); });
	}

	// ── data ──────────────────────────────────────────────────────────────────
	refresh() {
		frappe.call({
			method: "hotel_pms.hotel.api.get_room_board_data",
			callback: r => {
				if (!r.message) return;
				this._all_rooms = r.message;
				this._populate_filters();
				this._render();
			},
		});
	}

	_populate_filters() {
		const types  = [...new Set(this._all_rooms.map(r => r.room_type).filter(Boolean))].sort();
		const floors = [...new Set(this._all_rooms.map(r => String(r.floor || "")).filter(Boolean))].sort((a,b) => +a - +b);

		const $type  = this.wrapper.find("#rb-f-type");
		const $floor = this.wrapper.find("#rb-f-floor");

		types.forEach(t => {
			if (!$type.find(`option[value="${t}"]`).length)
				$type.append(`<option value="${t}">${t}</option>`);
		});
		floors.forEach(f => {
			if (!$floor.find(`option[value="${f}"]`).length)
				$floor.append(`<option value="${f}">${__("Floor")} ${f}</option>`);
		});
	}

	// ── filter + render ────────────────────────────────────────────────────────
	_render() {
		const f = this.filters;
		const rooms = this._all_rooms.filter(r => {
			if (f.status !== "All" && r.status !== f.status) return false;
			if (f.hk     !== "All" && r.housekeeping_status !== f.hk) return false;
			if (f.type   !== "All" && r.room_type !== f.type) return false;
			if (f.floor  !== "All" && String(r.floor || "") !== f.floor) return false;
			if (f.q) {
				const hay = (r.room_number + " " + (r.guest_name || "")).toLowerCase();
				if (!hay.includes(f.q)) return false;
			}
			return true;
		});

		this._render_summary(rooms);
		this._render_grid(rooms);
	}

	_render_summary(rooms) {
		const counts = {};
		rooms.forEach(r => { counts[r.status] = (counts[r.status] || 0) + 1; });

		const tiles = [
			{ lbl: __("Total Rooms"), val: rooms.length, color: "var(--text-color)" },
			{ lbl: __("Vacant"),      val: counts["Available"]     || 0, color: "#2da44e" },
			{ lbl: __("Reserved"),    val: counts["Reserved"]      || 0, color: "#1f6feb" },
			{ lbl: __("Occupied"),    val: counts["Occupied"]      || 0, color: "#e36209" },
			{ lbl: __("Dirty"),       val: counts["Dirty"]         || 0, color: "#d29922" },
			{ lbl: __("Cleaning"),    val: counts["Cleaning"]      || 0, color: "#8b5cf6" },
			{ lbl: __("Out of Service"), val: counts["Out of Service"] || 0, color: "#6e7681" },
		];

		this.wrapper.find("#rb-summary").html(
			tiles.map(t => `
<div class="rb-summary-tile">
  <span class="val" style="color:${t.color};">${t.val}</span>
  <span class="lbl">${t.lbl}</span>
</div>`).join(""));
	}

	_render_grid(rooms) {
		if (!rooms.length) {
			this.wrapper.find("#rb-grid").html(`<div class="text-muted p-4">${__("No rooms match the current filters.")}</div>`);
			return;
		}

		const html = rooms.map(r => {
			const sc    = STATUS_COLOR[r.status] || STATUS_COLOR["Available"];
			const hkCol = HK_DOT[r.housekeeping_status] || "#6e7681";
			const bal   = r.balance ? format_currency(r.balance) : __("Sh 0.00");
			const guest = r.guest_name || "—";
			const hasStay = !!r.stay;

			return `
<div class="rb-card" data-room="${r.name}" data-stay="${r.stay || ""}"
     style="border-top-color:${sc.border};">
  <div class="rb-card-head">
    <div>
      <div class="rb-room-num">${__("Room")} ${r.room_number}</div>
      <div class="rb-room-type">${r.room_type_name || r.room_type || ""}</div>
    </div>
    <span class="rb-badge" style="background:${sc.badge};">${__(sc.label)}</span>
  </div>
  <div class="rb-row">
    <span class="rb-row-lbl">${__("Floor")}</span>
    <span class="rb-row-val">${r.floor || "—"}</span>
  </div>
  <div class="rb-row">
    <span class="rb-row-lbl">${__("Housekeeping")}</span>
    <span class="rb-row-val">
      <span class="rb-hk-dot" style="background:${hkCol};"></span>
      ${r.housekeeping_status || "—"}
    </span>
  </div>
  <div class="rb-row">
    <span class="rb-row-lbl">${__("Guest")}</span>
    <span class="rb-row-val">${guest}</span>
  </div>
  <div class="rb-row">
    <span class="rb-row-lbl">${__("Balance")}</span>
    <span class="rb-row-val">${bal}</span>
  </div>
  <div class="rb-actions">
    <button class="rb-btn btn-open-room">${__("Open Room")}</button>
    ${hasStay ? `<button class="rb-btn rb-btn-primary btn-open-stay">${__("Open Stay")}</button>` : ""}
  </div>
</div>`;
		}).join("");

		const $grid = this.wrapper.find("#rb-grid").html(html);

		$grid.find(".btn-open-room").on("click", function (e) {
			e.stopPropagation();
			frappe.set_route("Form", "Hotel Room", $(this).closest(".rb-card").data("room"));
		});
		$grid.find(".btn-open-stay").on("click", function (e) {
			e.stopPropagation();
			frappe.set_route("Form", "Hotel Stay", $(this).closest(".rb-card").data("stay"));
		});
		$grid.find(".rb-card").on("click", function () {
			frappe.set_route("Form", "Hotel Room", $(this).data("room"));
		});
	}
}
