frappe.pages["room-board"].on_page_load = function (wrapper) {
    var page = frappe.ui.make_app_page({
        parent: wrapper,
        title: "Room Board",
        single_column: true,
    });

    page.add_action_item(__("Refresh"), () => load_board());
    page.add_action_item(__("Seed Demo Data"), () => {
        frappe.set_route("room-board");
        window.location.href = "/hotel-pms/seed-demo-data";
    });

    const $container = $('<div class="room-board-container" style="padding:16px"></div>').appendTo(page.main);

    function load_board() {
        $container.html('<div class="text-muted text-center" style="padding:40px">Loading...</div>');
        frappe.call({
            method: "hotel_pms.api.room_board.get_room_board",
            callback: function (r) {
                render_board(r.message || []);
            }
        });
        frappe.call({
            method: "hotel_pms.api.room_board.get_room_stats",
            callback: function (r) {
                render_kpis(r.message || {});
            }
        });
    }

    function render_kpis(stats) {
        const kpi_html = `
            <div class="row" style="margin-bottom:16px">
                <div class="col-sm-2">
                    <div class="card text-center p-3 bg-light">
                        <h2 class="text-primary">${stats.total_rooms || 0}</h2>
                        <small>Total Rooms</small>
                    </div>
                </div>
                <div class="col-sm-2">
                    <div class="card text-center p-3" style="background:#e8f5e9">
                        <h2 class="text-success">${stats.available || 0}</h2>
                        <small>Available</small>
                    </div>
                </div>
                <div class="col-sm-2">
                    <div class="card text-center p-3" style="background:#e3f2fd">
                        <h2 class="text-info">${stats.occupied || 0}</h2>
                        <small>Occupied</small>
                    </div>
                </div>
                <div class="col-sm-2">
                    <div class="card text-center p-3" style="background:#fff3e0">
                        <h2 class="text-warning">${stats.occupancy_pct || 0}%</h2>
                        <small>Occupancy</small>
                    </div>
                </div>
                <div class="col-sm-2">
                    <div class="card text-center p-3" style="background:#f3e5f5">
                        <h2 class="text-purple">${stats.arrivals_today || 0}</h2>
                        <small>Arrivals Today</small>
                    </div>
                </div>
                <div class="col-sm-2">
                    <div class="card text-center p-3" style="background:#fce4ec">
                        <h2 class="text-danger">${stats.departures_today || 0}</h2>
                        <small>Departures Today</small>
                    </div>
                </div>
            </div>`;
        $container.prepend(kpi_html);
    }

    function render_board(rooms) {
        if (!rooms.length) {
            $container.html('<div class="text-muted text-center" style="padding:40px">No rooms found. <a href="/app/hotel-room/new">Add a room</a> or <a href="/hotel-pms/seed-demo-data">seed demo data</a>.</div>');
            return;
        }

        // Group by floor
        const floors = {};
        rooms.forEach(r => {
            const fl = r.floor || "0";
            if (!floors[fl]) floors[fl] = [];
            floors[fl].push(r);
        });

        const STATUS_COLORS = {
            Available: "#4caf50",
            Occupied: "#2196f3",
            Reserved: "#ff9800",
            Cleaning: "#ffeb3b",
            Dirty: "#9e9e9e",
            Maintenance: "#f44336",
            "Out of Service": "#880000",
            Blocked: "#7b1fa2",
        };

        let html = '<div class="room-board">';
        Object.keys(floors).sort((a,b)=>a-b).forEach(fl => {
            html += `<h5 style="margin-top:20px;border-bottom:1px solid #eee;padding-bottom:6px">Floor ${fl}</h5>
                     <div class="room-grid" style="display:flex;flex-wrap:wrap;gap:10px;margin-bottom:8px">`;
            floors[fl].forEach(room => {
                const color = STATUS_COLORS[room.status] || "#ccc";
                const text_color = ["Dirty","Cleaning","Reserved"].includes(room.status) ? "#333" : "#fff";
                const guest = room.guest_name ? `<div style="font-size:10px;overflow:hidden;white-space:nowrap;max-width:100px">${room.guest_name}</div>` : "";
                const checkout = room.expected_checkout ? `<div style="font-size:10px">CO: ${room.expected_checkout.substring(0,10)}</div>` : "";
                html += `
                    <div class="room-card" title="${room.status}"
                         style="background:${color};color:${text_color};padding:10px;border-radius:6px;width:110px;min-height:80px;cursor:pointer;box-shadow:0 1px 3px rgba(0,0,0,.2)"
                         data-room="${room.name}" data-stay="${room.stay_name || ''}">
                        <div style="font-size:14px;font-weight:bold">${room.room_number || room.name}</div>
                        <div style="font-size:10px">${room.room_type_name || ""}</div>
                        ${guest}${checkout}
                        <div style="font-size:10px;margin-top:4px">${room.status}</div>
                    </div>`;
            });
            html += "</div>";
        });
        html += "</div>";

        // Legend
        html += '<div style="display:flex;flex-wrap:wrap;gap:8px;margin-top:16px">';
        Object.entries(STATUS_COLORS).forEach(([s,c]) => {
            html += `<span style="background:${c};color:#fff;padding:2px 8px;border-radius:10px;font-size:11px">${s}</span>`;
        });
        html += "</div>";

        $container.html(html);

        // Click handler
        $container.find(".room-card").on("click", function () {
            const stay = $(this).data("stay");
            const room = $(this).data("room");
            if (stay) frappe.set_route("Form", "Hotel Stay", stay);
            else frappe.set_route("Form", "Hotel Room", room);
        });
    }

    // Auto-refresh every 60 seconds
    load_board();
    setInterval(load_board, 60000);
};
