// Hotel PMS — Main JavaScript Bundle
// Provides: hotel_pms.dashboard, hotel_pms.room_board, hotel_pms.room_planner, hotel_pms.test_data

frappe.provide('hotel_pms');
frappe.provide('hotel_pms.dashboard');
frappe.provide('hotel_pms.room_board');
frappe.provide('hotel_pms.room_planner');
frappe.provide('hotel_pms.test_data');

// ─────────────────────────────────────────
// UTILITIES
// ─────────────────────────────────────────
hotel_pms.status_color = function(status) {
    return {
        'Available': '#22c55e', 'Vacant': '#22c55e',
        'Reserved':  '#3b82f6',
        'Occupied':  '#f97316',
        'Cleaning':  '#a855f7',
        'Dirty':     '#ef4444',
        'Maintenance': '#6b7280',
        'Blocked':   '#1f2937',
        'Out of Service': '#374151',
        'Confirmed': '#3b82f6',
        'Draft':     '#9ca3af',
        'Checked In':'#f97316',
        'Checked Out':'#22c55e',
        'Cancelled': '#ef4444'
    }[status] || '#9ca3af';
};

hotel_pms.status_badge = function(status) {
    const color = hotel_pms.status_color(status);
    return `<span class="hpms-badge" style="background:${color};color:#fff;padding:2px 8px;border-radius:10px;font-size:11px;font-weight:600;">${status}</span>`;
};

hotel_pms.fmt_currency = function(v) {
    return frappe.format(v || 0, {fieldtype: 'Currency'});
};

hotel_pms.fmt_date = function(d) {
    return d ? frappe.datetime.str_to_user(d) : '-';
};

// ─────────────────────────────────────────
// DASHBOARD
// ─────────────────────────────────────────
hotel_pms.dashboard = {
    page: null,

    init: function(page) {
        this.page = page;
        page.set_secondary_action('Refresh', () => this.refresh(), 'refresh');
        this.refresh();
    },

    refresh: function() {
        frappe.call({
            method: 'hotel_pms.api.dashboard.get_dashboard_stats',
            callback: (r) => {
                if (r.message) this.render(r.message);
            }
        });
    },

    render: function(stats) {
        const cards = [
            {label: 'Available Rooms',   value: stats.available_rooms,   color: '#22c55e', icon: '🟢', route: ['List','Hotel Room',{status:'Available'}]},
            {label: 'Occupied Rooms',    value: stats.occupied_rooms,    color: '#f97316', icon: '🟠', route: ['List','Hotel Room',{status:'Occupied'}]},
            {label: 'Reserved Rooms',    value: stats.reserved_rooms,    color: '#3b82f6', icon: '🔵', route: ['List','Hotel Room',{status:'Reserved'}]},
            {label: 'Cleaning Rooms',    value: stats.cleaning_rooms,    color: '#a855f7', icon: '🟣', route: ['List','Hotel Room',{status:'Cleaning'}]},
            {label: "Today's Arrivals",  value: stats.today_arrivals,    color: '#06b6d4', icon: '📥', route: ['List','Hotel Reservation',{arrival_date:frappe.datetime.get_today()}]},
            {label: "Today's Departures",value: stats.today_departures,  color: '#ec4899', icon: '📤', route: ['List','Hotel Stay',{expected_checkout:frappe.datetime.get_today(),status:'Active'}]},
            {label: 'Active Stays',      value: stats.active_stays,      color: '#f59e0b', icon: '🏨', route: ['List','Hotel Stay',{status:'Active'}]},
            {label: 'Total Reservations',value: stats.total_reservations, color: '#6366f1', icon: '📋', route: ['List','Hotel Reservation']},
            {label: 'Pending Housekeeping',value: stats.pending_housekeeping, color: '#ef4444', icon: '🧹', route: ['List','Hotel Housekeeping',{status:['Dirty','Cleaning']}]},
        ];

        const cardsHtml = cards.map(c => `
            <div class="hpms-stat-card" data-route='${JSON.stringify(c.route)}' style="border-top:4px solid ${c.color}">
                <div class="hpms-stat-icon">${c.icon}</div>
                <div class="hpms-stat-value" style="color:${c.color}">${c.value}</div>
                <div class="hpms-stat-label">${c.label}</div>
            </div>
        `).join('');

        const quickLinks = [
            {label:'New Reservation', route:['Form','Hotel Reservation','new-hotel-reservation-1'], icon:'📝'},
            {label:'Room Board',      route:['hotel-pms-room-board'], icon:'🏢', page:true},
            {label:'Room Planner',    route:['hotel-pms-room-planner'], icon:'📅', page:true},
            {label:'Housekeeping',    route:['List','Hotel Housekeeping',{status:['Dirty','Cleaning']}], icon:'🧹'},
            {label:'Payments',        route:['List','Hotel Payment'], icon:'💳'},
            {label:'Test Data',       route:['hotel-pms-test-data'], icon:'🧪', page:true},
        ];

        const linksHtml = quickLinks.map(l => `
            <button class="btn btn-default hpms-quick-btn" data-route='${JSON.stringify(l.route)}' data-page="${l.page||false}">
                ${l.icon} ${l.label}
            </button>
        `).join('');

        const outerBalance = stats.outstanding_balance > 0
            ? `<div class="hpms-alert">💰 Outstanding balance: <strong>${hotel_pms.fmt_currency(stats.outstanding_balance)}</strong></div>`
            : '';

        const html = `
            <style>
                .hpms-dashboard { padding: 16px; }
                .hpms-section-title { font-size: 13px; font-weight: 700; color: var(--text-muted); text-transform: uppercase; letter-spacing: 1px; margin: 20px 0 10px; }
                .hpms-stats-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(160px, 1fr)); gap: 12px; }
                .hpms-stat-card { background: var(--card-bg); border-radius: 8px; padding: 16px 14px; cursor: pointer; transition: box-shadow .15s; }
                .hpms-stat-card:hover { box-shadow: 0 4px 16px rgba(0,0,0,.12); }
                .hpms-stat-icon { font-size: 22px; margin-bottom: 6px; }
                .hpms-stat-value { font-size: 32px; font-weight: 700; line-height: 1; }
                .hpms-stat-label { font-size: 12px; color: var(--text-muted); margin-top: 4px; }
                .hpms-quick-links { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 8px; }
                .hpms-quick-btn { border-radius: 6px !important; font-size: 13px; }
                .hpms-alert { background: #fef3c7; border: 1px solid #fcd34d; border-radius: 6px; padding: 10px 14px; margin-top: 12px; font-size: 13px; }
            </style>
            <div class="hpms-dashboard">
                <div class="hpms-section-title">Overview</div>
                <div class="hpms-stats-grid">${cardsHtml}</div>
                ${outerBalance}
                <div class="hpms-section-title">Quick Actions</div>
                <div class="hpms-quick-links">${linksHtml}</div>
            </div>
        `;

        $('#hotel-dashboard').html(html);

        // Bind stat card clicks
        $('#hotel-dashboard .hpms-stat-card').on('click', function() {
            const route = JSON.parse($(this).attr('data-route'));
            frappe.set_route(...route);
        });

        // Bind quick link clicks
        $('#hotel-dashboard .hpms-quick-btn').on('click', function() {
            const route = JSON.parse($(this).attr('data-route'));
            const isPage = $(this).data('page') === true || $(this).data('page') === 'true';
            if (isPage) {
                frappe.set_route(route[0]);
            } else {
                frappe.set_route(...route);
            }
        });
    }
};

// ─────────────────────────────────────────
// ROOM BOARD
// ─────────────────────────────────────────
hotel_pms.room_board = {
    page: null,
    filters: {status: 'All', housekeeping: 'All', room_type: 'All', floor: 'All', search: ''},
    all_rooms: [],

    init: function(page) {
        this.page = page;
        this.render_filters(page);
        this.load();
    },

    render_filters: function(page) {
        const filterHtml = `
            <style>
                .rb-filters { display:flex; flex-wrap:wrap; gap:8px; padding:12px 16px; background:var(--card-bg); border-bottom:1px solid var(--border-color); }
                .rb-filter-group { display:flex; flex-direction:column; gap:2px; }
                .rb-filter-group label { font-size:11px; color:var(--text-muted); font-weight:600; }
                .rb-filter-group select, .rb-filter-group input { border:1px solid var(--border-color); border-radius:4px; padding:4px 8px; font-size:13px; background:var(--control-bg); color:var(--text-color); min-width:110px; }
                .rb-stats { display:flex; gap:16px; padding:10px 16px; background:var(--bg-color); border-bottom:1px solid var(--border-color); flex-wrap:wrap; }
                .rb-stat { display:flex; align-items:center; gap:6px; font-size:13px; }
                .rb-stat-dot { width:10px; height:10px; border-radius:50%; }
                .rb-stat-val { font-weight:700; }
                .rb-cards { display:grid; grid-template-columns:repeat(auto-fill,minmax(220px,1fr)); gap:12px; padding:16px; }
                .rb-card { background:var(--card-bg); border-radius:8px; border-top:4px solid #ccc; padding:14px; position:relative; }
                .rb-card-header { display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:8px; }
                .rb-room-num { font-size:18px; font-weight:700; }
                .rb-room-type { font-size:11px; color:var(--text-muted); margin-top:1px; }
                .rb-field { font-size:12px; color:var(--text-color); margin:3px 0; }
                .rb-field span { color:var(--text-muted); }
                .rb-actions { margin-top:10px; display:flex; gap:6px; flex-wrap:wrap; }
                .rb-btn { font-size:11px; padding:3px 10px; border-radius:4px; border:1px solid var(--border-color); background:var(--control-bg); cursor:pointer; }
                .rb-btn:hover { background:var(--btn-default-hover-bg); }
                .rb-btn-primary { background:var(--primary); color:#fff; border-color:var(--primary); }
            </style>
            <div class="rb-filters">
                <div class="rb-filter-group">
                    <label>Status</label>
                    <select id="rb-status">
                        <option value="All">All</option>
                        <option value="Available">Available</option>
                        <option value="Reserved">Reserved</option>
                        <option value="Occupied">Occupied</option>
                        <option value="Cleaning">Cleaning</option>
                        <option value="Maintenance">Maintenance</option>
                    </select>
                </div>
                <div class="rb-filter-group">
                    <label>Housekeeping</label>
                    <select id="rb-hk">
                        <option value="All">All</option>
                        <option value="Clean">Clean</option>
                        <option value="Dirty">Dirty</option>
                        <option value="Cleaning">Cleaning</option>
                    </select>
                </div>
                <div class="rb-filter-group">
                    <label>Room Type</label>
                    <select id="rb-rtype">
                        <option value="All">All</option>
                    </select>
                </div>
                <div class="rb-filter-group">
                    <label>Floor</label>
                    <select id="rb-floor">
                        <option value="All">All</option>
                    </select>
                </div>
                <div class="rb-filter-group">
                    <label>Search</label>
                    <input type="text" id="rb-search" placeholder="Room number or guest name" style="min-width:200px">
                </div>
            </div>
        `;

        const container = $('#room-board-container');
        container.html(filterHtml + `
            <div id="rb-stats" class="rb-stats"></div>
            <div id="rb-cards" class="rb-cards"><div class="text-center py-5 text-muted">Loading rooms...</div></div>
        `);

        const self = this;
        $('#rb-status, #rb-hk, #rb-rtype, #rb-floor').on('change', function() {
            self.filters.status = $('#rb-status').val();
            self.filters.housekeeping = $('#rb-hk').val();
            self.filters.room_type = $('#rb-rtype').val();
            self.filters.floor = $('#rb-floor').val();
            self.render_cards();
        });
        let searchTimer;
        $('#rb-search').on('input', function() {
            clearTimeout(searchTimer);
            searchTimer = setTimeout(() => {
                self.filters.search = $(this).val().toLowerCase();
                self.render_cards();
            }, 200);
        });
    },

    load: function() {
        frappe.call({
            method: 'hotel_pms.api.dashboard.get_room_board',
            callback: (r) => {
                if (r.message) {
                    this.all_rooms = r.message;
                    this.populate_filter_options();
                    this.render_stats();
                    this.render_cards();
                }
            }
        });
    },

    populate_filter_options: function() {
        const types = [...new Set(this.all_rooms.map(r => r.room_type).filter(Boolean))].sort();
        const floors = [...new Set(this.all_rooms.map(r => r.floor).filter(v => v !== null))].sort((a,b)=>a-b);

        const rtSelect = $('#rb-rtype');
        const floorSelect = $('#rb-floor');
        types.forEach(t => rtSelect.append(`<option value="${t}">${t}</option>`));
        floors.forEach(f => floorSelect.append(`<option value="${f}">Floor ${f}</option>`));
    },

    render_stats: function() {
        const counts = {};
        this.all_rooms.forEach(r => { counts[r.status] = (counts[r.status]||0)+1; });
        const items = Object.entries(counts).map(([s,c]) =>
            `<div class="rb-stat"><div class="rb-stat-dot" style="background:${hotel_pms.status_color(s)}"></div>
             <span>${s}</span><span class="rb-stat-val">${c}</span></div>`
        ).join('');
        $('#rb-stats').html(`<div class="rb-stat"><span>Total Rooms</span><span class="rb-stat-val">${this.all_rooms.length}</span></div>` + items);
    },

    render_cards: function() {
        const f = this.filters;
        let rooms = this.all_rooms.filter(r => {
            if (f.status !== 'All' && r.status !== f.status) return false;
            if (f.housekeeping !== 'All' && r.housekeeping_status !== f.housekeeping) return false;
            if (f.room_type !== 'All' && r.room_type !== f.room_type) return false;
            if (f.floor !== 'All' && String(r.floor) !== f.floor) return false;
            if (f.search) {
                const q = f.search;
                if (!((r.room_number||'').toLowerCase().includes(q) ||
                      (r.guest_name||'').toLowerCase().includes(q))) return false;
            }
            return true;
        });

        if (!rooms.length) {
            $('#rb-cards').html('<div class="text-center py-5 text-muted">No rooms match filters</div>');
            return;
        }

        const html = rooms.map(r => {
            const color = hotel_pms.status_color(r.status);
            const guestInfo = r.stay_name ? `
                <div class="rb-field"><span>Guest:</span> ${r.guest_name || r.stay_customer || '-'}</div>
                <div class="rb-field"><span>Balance:</span> ${hotel_pms.fmt_currency(r.folio_balance)}</div>
            ` : `<div class="rb-field" style="color:var(--text-muted)">No active guest</div>`;

            const hkBadge = r.housekeeping_status
                ? `<span style="font-size:10px;background:${hotel_pms.status_color(r.housekeeping_status)};color:#fff;padding:1px 6px;border-radius:8px;">${r.housekeeping_status}</span>`
                : '';

            const actions = r.stay_name
                ? `<button class="rb-btn rb-btn-primary" onclick="frappe.set_route('Form','Hotel Stay','${r.stay_name}')">Open Stay</button>
                   <button class="rb-btn" onclick="frappe.set_route('Form','Hotel Room','${r.name}')">Room</button>`
                : `<button class="rb-btn" onclick="frappe.set_route('Form','Hotel Room','${r.name}')">Open Room</button>`;

            return `
                <div class="rb-card" style="border-top-color:${color}">
                    <div class="rb-card-header">
                        <div>
                            <div class="rb-room-num">Room ${r.room_number}</div>
                            <div class="rb-room-type">${r.room_type || ''}</div>
                        </div>
                        ${hotel_pms.status_badge(r.status)}
                    </div>
                    <div class="rb-field"><span>Floor:</span> ${r.floor ?? '-'}</div>
                    <div class="rb-field"><span>Housekeeping:</span> ${r.housekeeping_status || 'Clean'} ${hkBadge}</div>
                    ${guestInfo}
                    <div class="rb-actions">${actions}</div>
                </div>
            `;
        }).join('');

        $('#rb-cards').html(html);
    }
};

// ─────────────────────────────────────────
// ROOM PLANNER (Planning Board)
// ─────────────────────────────────────────
hotel_pms.room_planner = {
    page: null,
    data: null,
    from_date: null,
    filters: {room: 'All', room_type: 'All', status: 'All', customer: ''},

    init: function(page) {
        this.page = page;
        this.from_date = frappe.datetime.get_today();
        this.render_controls(page);
        this.load();
    },

    render_controls: function(page) {
        const container = $('#room-planner-container');
        const roomParam = frappe.utils.get_url_state('room');

        container.html(`
            <style>
                .rp-controls { display:flex; flex-wrap:wrap; gap:8px; padding:12px 16px; background:var(--card-bg); border-bottom:1px solid var(--border-color); align-items:flex-end; }
                .rp-ctrl-group { display:flex; flex-direction:column; gap:2px; }
                .rp-ctrl-group label { font-size:11px; font-weight:600; color:var(--text-muted); }
                .rp-ctrl-group input, .rp-ctrl-group select { border:1px solid var(--border-color); border-radius:4px; padding:4px 8px; font-size:13px; background:var(--control-bg); color:var(--text-color); }
                .rp-nav { display:flex; gap:4px; }
                .rp-nav-btn { border:1px solid var(--border-color); border-radius:4px; padding:4px 12px; background:var(--control-bg); cursor:pointer; font-size:13px; }
                .rp-nav-btn:hover { background:var(--btn-default-hover-bg); }
                .rp-scroll { overflow-x:auto; padding:16px; }
                .rp-table { border-collapse:collapse; min-width:100%; font-size:12px; }
                .rp-table th { background:var(--card-bg); border:1px solid var(--border-color); padding:6px 10px; text-align:center; white-space:nowrap; position:sticky; top:0; z-index:2; }
                .rp-table th.room-col { text-align:left; min-width:120px; position:sticky; left:0; z-index:3; }
                .rp-table td { border:1px solid var(--border-color); padding:0; height:36px; min-width:60px; text-align:center; vertical-align:middle; position:relative; }
                .rp-table td.room-label { padding:6px 10px; text-align:left; background:var(--card-bg); position:sticky; left:0; z-index:1; white-space:nowrap; font-weight:600; }
                .rp-cell { display:flex; align-items:center; justify-content:center; width:100%; height:100%; font-size:10px; font-weight:600; cursor:pointer; }
                .rp-legend { display:flex; gap:12px; flex-wrap:wrap; padding:8px 16px; font-size:11px; }
                .rp-legend-item { display:flex; align-items:center; gap:4px; }
                .rp-legend-dot { width:10px; height:10px; border-radius:2px; }
                .rp-res-bar { border-radius:3px; margin:2px; padding:2px 4px; font-size:10px; color:#fff; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; max-width:100%; cursor:pointer; }
                .rp-today { background:#fef3c7 !important; }
            </style>
            <div class="rp-controls">
                <div class="rp-ctrl-group">
                    <label>From Date</label>
                    <input type="date" id="rp-from-date" value="${this.from_date}">
                </div>
                <div class="rp-ctrl-group">
                    <label>Days</label>
                    <select id="rp-days">
                        <option value="7">7 days</option>
                        <option value="14" selected>14 days</option>
                        <option value="21">21 days</option>
                        <option value="30">30 days</option>
                    </select>
                </div>
                <div class="rp-ctrl-group">
                    <label>Room Type</label>
                    <select id="rp-rtype"><option value="All">All Types</option></select>
                </div>
                <div class="rp-ctrl-group">
                    <label>Room</label>
                    <select id="rp-room"><option value="All">All Rooms</option></select>
                    ${roomParam ? `<script>setTimeout(()=>{ $('#rp-room').val('${roomParam}'); hotel_pms.room_planner.apply_filters(); },500)</script>` : ''}
                </div>
                <div class="rp-ctrl-group">
                    <label>&nbsp;</label>
                    <div class="rp-nav">
                        <button class="rp-nav-btn" id="rp-prev">◀ Prev</button>
                        <button class="rp-nav-btn" id="rp-today-btn">Today</button>
                        <button class="rp-nav-btn" id="rp-next">Next ▶</button>
                        <button class="rp-nav-btn" id="rp-refresh">↻</button>
                    </div>
                </div>
            </div>
            <div class="rp-legend">
                ${['Available','Reserved','Occupied','Cleaning','Maintenance','Blocked'].map(s =>
                    `<div class="rp-legend-item"><div class="rp-legend-dot" style="background:${hotel_pms.status_color(s)}"></div>${s}</div>`
                ).join('')}
            </div>
            <div class="rp-scroll">
                <div id="rp-grid">Loading...</div>
            </div>
        `);

        const self = this;

        $('#rp-from-date').on('change', function() {
            self.from_date = $(this).val();
            self.load();
        });
        $('#rp-days').on('change', () => self.load());
        $('#rp-rtype, #rp-room').on('change', () => self.render_grid());

        $('#rp-prev').on('click', function() {
            const days = parseInt($('#rp-days').val());
            self.from_date = frappe.datetime.add_days(self.from_date, -days);
            $('#rp-from-date').val(self.from_date);
            self.load();
        });
        $('#rp-today-btn').on('click', function() {
            self.from_date = frappe.datetime.get_today();
            $('#rp-from-date').val(self.from_date);
            self.load();
        });
        $('#rp-next').on('click', function() {
            const days = parseInt($('#rp-days').val());
            self.from_date = frappe.datetime.add_days(self.from_date, days);
            $('#rp-from-date').val(self.from_date);
            self.load();
        });
        $('#rp-refresh').on('click', () => self.load());
    },

    load: function() {
        const days = parseInt($('#rp-days').val() || 14);
        const to_date = frappe.datetime.add_days(this.from_date, days);

        frappe.call({
            method: 'hotel_pms.api.dashboard.get_room_planner',
            args: {from_date: this.from_date, to_date: to_date},
            callback: (r) => {
                if (r.message) {
                    this.data = r.message;
                    this.populate_room_filter();
                    this.render_grid();
                }
            }
        });
    },

    populate_room_filter: function() {
        if (!this.data) return;
        const rooms = this.data.rooms || [];
        const types = [...new Set(rooms.map(r => r.room_type).filter(Boolean))].sort();
        const rtSel = $('#rp-rtype');
        rtSel.find('option:not(:first)').remove();
        types.forEach(t => rtSel.append(`<option value="${t}">${t}</option>`));

        const rmSel = $('#rp-room');
        rmSel.find('option:not(:first)').remove();
        rooms.forEach(r => rmSel.append(`<option value="${r.name}">Room ${r.room_number}</option>`));
    },

    render_grid: function() {
        if (!this.data) return;

        const rtFilter = $('#rp-rtype').val() || 'All';
        const rmFilter = $('#rp-room').val() || 'All';
        const days = parseInt($('#rp-days').val() || 14);
        const today = frappe.datetime.get_today();

        // Build date array
        const dates = [];
        for (let i = 0; i < days; i++) {
            dates.push(frappe.datetime.add_days(this.from_date, i));
        }

        // Filter rooms
        let rooms = (this.data.rooms || []).filter(r => {
            if (rtFilter !== 'All' && r.room_type !== rtFilter) return false;
            if (rmFilter !== 'All' && r.name !== rmFilter) return false;
            return true;
        });

        // Build reservation map: room -> [{arrival, departure, ...}]
        const resMap = {};
        (this.data.reservations || []).forEach(res => {
            if (!resMap[res.room]) resMap[res.room] = [];
            resMap[res.room].push(res);
        });

        // Build housekeeping map: room+date -> status
        const hkMap = {};
        (this.data.housekeeping || []).forEach(hk => {
            hkMap[`${hk.room}_${hk.date}`] = hk.status;
        });

        // Determine cell status
        const getCellStatus = (room, date, reservations) => {
            for (const res of (reservations || [])) {
                if (date >= res.arrival_date && date < res.departure_date) {
                    return {type: 'reservation', res};
                }
            }
            const hk = hkMap[`${room.name}_${date}`];
            if (hk) return {type: 'housekeeping', status: hk};
            if (date === today) {
                if (['Occupied','Reserved','Cleaning','Maintenance','Blocked'].includes(room.status)) {
                    return {type: 'room_status', status: room.status};
                }
            }
            return {type: 'available'};
        };

        const headerHtml = `<th class="room-col">Room</th>` +
            dates.map(d => {
                const isToday = d === today;
                const label = frappe.datetime.str_to_user(d).slice(0,5);
                return `<th class="${isToday ? 'rp-today' : ''}">${label}</th>`;
            }).join('');

        const rowsHtml = rooms.map(room => {
            const roomRes = resMap[room.name] || [];

            const cells = dates.map(date => {
                const cell = getCellStatus(room, date, roomRes);
                const isToday = date === today;

                if (cell.type === 'reservation') {
                    const res = cell.res;
                    const color = hotel_pms.status_color(res.status);
                    const isStart = date === res.arrival_date;
                    const label = isStart ? (res.guest_name || res.customer || 'Guest').split(' ')[0] : '';
                    return `<td class="${isToday ? 'rp-today' : ''}">
                        <div class="rp-res-bar" style="background:${color}"
                             title="${res.guest_name||''} | ${res.arrival_date} → ${res.departure_date} | ${res.status}"
                             onclick="frappe.set_route('Form','Hotel Reservation','${res.reservation}')">
                            ${label}
                        </div>
                    </td>`;
                } else if (cell.type === 'housekeeping') {
                    const color = hotel_pms.status_color(cell.status);
                    return `<td class="${isToday ? 'rp-today' : ''}">
                        <div class="rp-cell" style="background:${color}22;color:${color}" title="${cell.status}">
                            ${cell.status.slice(0,4).toUpperCase()}
                        </div>
                    </td>`;
                } else if (cell.type === 'room_status') {
                    const color = hotel_pms.status_color(cell.status);
                    return `<td class="${isToday ? 'rp-today' : ''}">
                        <div class="rp-cell" style="background:${color}22;color:${color}" title="${cell.status}">
                            ${cell.status.slice(0,4).toUpperCase()}
                        </div>
                    </td>`;
                } else {
                    return `<td class="${isToday ? 'rp-today' : ''}">
                        <div class="rp-cell" style="color:#22c55e22" title="Available">FREE</div>
                    </td>`;
                }
            }).join('');

            return `<tr>
                <td class="room-label" title="${room.room_type||''} | Floor ${room.floor||''}">
                    <a href="#" onclick="frappe.set_route('Form','Hotel Room','${room.name}');return false;">
                        Room ${room.room_number}
                    </a>
                    <div style="font-size:10px;color:var(--text-muted)">${room.room_type||''}</div>
                </td>
                ${cells}
            </tr>`;
        }).join('');

        const tableHtml = `
            <table class="rp-table">
                <thead><tr>${headerHtml}</tr></thead>
                <tbody>${rowsHtml || '<tr><td colspan="99" class="text-center py-3 text-muted">No rooms</td></tr>'}</tbody>
            </table>
        `;

        $('#rp-grid').html(tableHtml);
    }
};

// ─────────────────────────────────────────
// TEST DATA MANAGER
// ─────────────────────────────────────────
hotel_pms.test_data = {
    page: null,

    init: function(page) {
        this.page = page;
        this.render(page);
    },

    render: function(page) {
        page.main.html(`
            <style>
                .td-page { max-width: 700px; margin: 30px auto; padding: 0 16px; }
                .td-header { font-size: 22px; font-weight: 700; margin-bottom: 6px; }
                .td-subtitle { color: var(--text-muted); font-size: 14px; margin-bottom: 24px; }
                .td-card { background: var(--card-bg); border: 1px solid var(--border-color); border-radius: 8px; padding: 20px; margin-bottom: 16px; }
                .td-card-title { font-weight: 700; font-size: 15px; margin-bottom: 6px; }
                .td-card-desc { font-size: 13px; color: var(--text-muted); margin-bottom: 14px; }
                .td-btn { padding: 8px 20px; border-radius: 6px; border: none; font-size: 14px; font-weight: 600; cursor: pointer; }
                .td-btn-add { background: var(--primary); color: #fff; }
                .td-btn-add:hover { opacity: 0.9; }
                .td-btn-del { background: #ef4444; color: #fff; margin-left: 8px; }
                .td-btn-del:hover { opacity: 0.9; }
                .td-log { margin-top: 14px; max-height: 240px; overflow-y: auto; background: var(--bg-color); border: 1px solid var(--border-color); border-radius: 4px; padding: 10px; font-size: 12px; font-family: monospace; }
                .td-log-item { padding: 2px 0; border-bottom: 1px solid var(--border-color); }
                .td-log-ok { color: #22c55e; }
                .td-log-err { color: #ef4444; }
                .td-includes { display: grid; grid-template-columns: 1fr 1fr; gap: 4px; font-size: 12px; color: var(--text-muted); }
                .td-includes div::before { content: '✓ '; color: #22c55e; }
                .td-warning { background: #fef3c7; border: 1px solid #fcd34d; border-radius: 6px; padding: 10px 14px; font-size: 13px; margin-top: 12px; }
            </style>
            <div class="td-page">
                <div class="td-header">🧪 Hotel PMS Test Data</div>
                <div class="td-subtitle">Create or remove demo data for testing the complete Hotel PMS workflow.</div>

                <div class="td-card">
                    <div class="td-card-title">Add Test Data</div>
                    <div class="td-card-desc">Creates a complete set of demo records. Safe to run multiple times — will not create duplicates.</div>
                    <div class="td-includes">
                        <div>Customer Categories</div><div>Family Types</div>
                        <div>Room Types (8)</div><div>Rooms (10)</div>
                        <div>Services (9)</div><div>Packages (6)</div>
                        <div>Customers (5)</div><div>Reservations (5)</div>
                        <div>Payments</div><div>Active Stay + Folio</div>
                    </div>
                    <div style="margin-top:14px">
                        <button class="td-btn td-btn-add" id="td-add-btn">➕ Add Test Data</button>
                    </div>
                    <div id="td-add-log" class="td-log" style="display:none"></div>
                </div>

                <div class="td-card">
                    <div class="td-card-title">Delete Test Data</div>
                    <div class="td-card-desc">Removes only records tagged as demo data. Your real data is never touched.</div>
                    <div class="td-warning">⚠️ This will permanently delete all demo records. A confirmation will be shown first.</div>
                    <div style="margin-top:14px">
                        <button class="td-btn td-btn-del" id="td-del-btn">🗑️ Delete Test Data</button>
                    </div>
                    <div id="td-del-log" class="td-log" style="display:none"></div>
                </div>
            </div>
        `);

        const self = this;

        $('#td-add-btn').on('click', function() {
            const btn = $(this);
            btn.prop('disabled', true).text('Creating...');
            $('#td-add-log').show().html('<div class="td-log-item">Starting...</div>');

            frappe.call({
                method: 'hotel_pms.api.seed.add_test_data',
                freeze: true,
                freeze_message: 'Creating demo data...',
                callback: function(r) {
                    btn.prop('disabled', false).text('➕ Add Test Data');
                    const res = r.message;
                    if (res && res.success) {
                        const items = (res.created || []).map(c =>
                            `<div class="td-log-item td-log-ok">✓ ${c}</div>`
                        ).join('');
                        $('#td-add-log').html(items || '<div class="td-log-item td-log-ok">No new records needed</div>');
                        frappe.show_alert({message: res.message || 'Test data created!', indicator: 'green'}, 5);
                    } else {
                        $('#td-add-log').html(`<div class="td-log-item td-log-err">✗ ${(res && res.error) || 'Unknown error'}</div>`);
                        frappe.show_alert({message: 'Error creating test data', indicator: 'red'}, 5);
                    }
                }
            });
        });

        $('#td-del-btn').on('click', function() {
            frappe.confirm(
                '<b>Delete all test data?</b><br>This will remove all records tagged as demo data.<br>Your real data will not be affected.',
                function() {
                    const btn = $('#td-del-btn');
                    btn.prop('disabled', true).text('Deleting...');
                    $('#td-del-log').show().html('<div class="td-log-item">Starting deletion...</div>');

                    frappe.call({
                        method: 'hotel_pms.api.seed.delete_test_data',
                        freeze: true,
                        freeze_message: 'Deleting demo data...',
                        callback: function(r) {
                            btn.prop('disabled', false).text('🗑️ Delete Test Data');
                            const res = r.message;
                            if (res && res.success) {
                                const items = (res.deleted || []).map(c =>
                                    `<div class="td-log-item td-log-err">✓ Deleted: ${c}</div>`
                                ).join('');
                                const errs = (res.errors || []).map(e =>
                                    `<div class="td-log-item td-log-err">⚠ ${e}</div>`
                                ).join('');
                                $('#td-del-log').html(items + errs || '<div class="td-log-item">Nothing to delete</div>');
                                frappe.show_alert({message: res.message || 'Test data deleted!', indicator: 'orange'}, 5);
                            } else {
                                $('#td-del-log').html(`<div class="td-log-item td-log-err">✗ Error</div>`);
                            }
                        }
                    });
                }
            );
        });
    }
};
