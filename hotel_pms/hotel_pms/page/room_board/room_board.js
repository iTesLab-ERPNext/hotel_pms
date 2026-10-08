frappe.pages['room_board'].on_page_load = function(wrapper) {
    const page = frappe.ui.make_app_page({
        parent: wrapper,
        title: 'Room Board',
        single_column: true
    });

    const $body = $(wrapper).find('.page-content');
    $body.html(`
        <div id="rb-stats" class="row mb-4"></div>
        <div id="rb-floors"></div>
    `);

    load_board();
    setInterval(load_board, 60000);

    function load_board() {
        frappe.call({
            method: 'hotel_pms.hotel_pms.api.room_board.get_room_stats',
            callback(r) { render_stats(r.message); }
        });
        frappe.call({
            method: 'hotel_pms.hotel_pms.api.room_board.get_room_board',
            callback(r) { render_floors(r.message); }
        });
    }

    function render_stats(s) {
        $('#rb-stats').html(`
            <div class="col"><div class="card text-center p-3"><b>${s.total}</b><br>Total</div></div>
            <div class="col"><div class="card text-center p-3 bg-success text-white"><b>${s.available}</b><br>Available</div></div>
            <div class="col"><div class="card text-center p-3 bg-danger text-white"><b>${s.occupied}</b><br>Occupied</div></div>
            <div class="col"><div class="card text-center p-3 bg-warning"><b>${s.dirty}</b><br>Dirty</div></div>
            <div class="col"><div class="card text-center p-3 bg-secondary text-white"><b>${s.maintenance}</b><br>Maintenance</div></div>
            <div class="col"><div class="card text-center p-3 bg-info text-white"><b>${s.occupancy_pct}%</b><br>Occupancy</div></div>
            <div class="col"><div class="card text-center p-3"><b>${s.arrivals_today}</b><br>Arrivals</div></div>
            <div class="col"><div class="card text-center p-3"><b>${s.departures_today}</b><br>Departures</div></div>
        `);
    }

    const STATUS_COLORS = {
        'Available': '#28a745',
        'Occupied': '#dc3545',
        'Dirty': '#ffc107',
        'Maintenance': '#6c757d',
        'Out of Order': '#343a40'
    };

    function render_floors(data) {
        const floors = data.floors || {};
        let html = '';
        Object.keys(floors).sort().forEach(floor => {
            html += `<h5 class="mt-4">Floor ${floor}</h5><div class="d-flex flex-wrap gap-2">`;
            floors[floor].forEach(room => {
                const color = STATUS_COLORS[room.status] || '#aaa';
                const guest = room.guest_name ? `<small>${room.guest_name}</small>` : '';
                const checkout = room.expected_checkout ? `<small>- ${room.expected_checkout}</small>` : '';
                html += `
                    <div class="room-card p-2 rounded text-center" style="width:110px;background:${color};color:${room.status==='Dirty'?'#000':'#fff'};cursor:pointer"
                         data-room="${room.name}" data-stay="${room.stay_name || ''}">
                        <b>${room.room_number}</b><br>
                        <small>${room.room_type_label || ''}</small><br>
                        ${guest}${checkout}
                    </div>`;
            });
            html += '</div>';
        });
        $('#rb-floors').html(html || '<p class="text-muted mt-4">No rooms found. Run Seed Demo Data first.</p>');

        $('#rb-floors').off('click', '.room-card').on('click', '.room-card', function() {
            const stay = $(this).data('stay');
            const room = $(this).data('room');
            if (stay) frappe.set_route('Form', 'Hotel Stay', stay);
            else frappe.set_route('Form', 'Hotel Room', room);
        });
    }
};
