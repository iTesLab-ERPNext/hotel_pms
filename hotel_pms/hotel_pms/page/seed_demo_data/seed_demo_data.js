frappe.pages['seed_demo_data'].on_page_load = function(wrapper) {
    const page = frappe.ui.make_app_page({
        parent: wrapper,
        title: 'Seed Demo Data',
        single_column: true
    });

    $(wrapper).find('.page-content').html(`
        <div class="container mt-4" style="max-width:700px">
            <p class="text-muted">Creates room types, rooms, services, booking sources, sample customers and reservations. Safe to run multiple times - existing records are skipped.</p>
            <button id="btn-seed" class="btn btn-primary btn-lg mb-4">
                <i class="fa fa-database"></i> Seed All Demo Data
            </button>
            <div id="seed-results"></div>
        </div>
    `);

    $('#btn-seed').on('click', function() {
        const $btn = $(this);
        $btn.prop('disabled', true).text('Seeding...');
        frappe.call({
            method: 'hotel_pms.hotel_pms.api.seed_data.seed_all',
            callback(r) {
                $btn.prop('disabled', false).html('<i class="fa fa-database"></i> Seed All Demo Data');
                if (!r.message) return;
                const results = r.message;
                let html = '<table class="table table-bordered"><thead><tr><th>Category</th><th>Created</th><th>Skipped</th></tr></thead><tbody>';
                for (const [key, val] of Object.entries(results)) {
                    const label = key.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
                    html += `<tr>
                        <td>${label}</td>
                        <td><span class="badge badge-success">${val.created || 0}</span></td>
                        <td><span class="badge badge-secondary">${val.skipped || 0}</span></td>
                    </tr>`;
                }
                html += '</tbody></table>';
                html += '<div class="alert alert-success mt-2">Done! Go to <a href="/app/room_board">Room Board</a> to see the live view.</div>';
                $('#seed-results').html(html);
            }
        });
    });
};
