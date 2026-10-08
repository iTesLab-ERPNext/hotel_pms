frappe.pages["seed-demo-data"].on_page_load = function (wrapper) {
    var page = frappe.ui.make_app_page({
        parent: wrapper,
        title: "Seed Demo Data",
        single_column: true,
    });

    const $main = page.main;

    $main.html(`
        <div style="max-width:700px;margin:40px auto;padding:24px;background:#fff;border-radius:8px;box-shadow:0 1px 6px rgba(0,0,0,.1)">
            <h3>Hotel PMS — Demo Data</h3>
            <p class="text-muted">
                This will create sample Room Types, Rooms, Services, Booking Sources,
                Customers and Reservations. All operations are idempotent — safe to run multiple times.
            </p>
            <button class="btn btn-primary btn-lg" id="seed-btn">
                <i class="fa fa-magic"></i>&nbsp; Seed Demo Data
            </button>
            <div id="seed-results" style="margin-top:24px"></div>
        </div>
    `);

    $main.find("#seed-btn").on("click", function () {
        const $btn = $(this);
        $btn.prop("disabled", true).text("Seeding…");
        $main.find("#seed-results").html('<div class="text-muted">Running…</div>');

        frappe.call({
            method: "hotel_pms.api.seed_data.seed_all",
            callback: function (r) {
                $btn.prop("disabled", false).html('<i class="fa fa-magic"></i>&nbsp; Seed Demo Data');
                const results = r.message || [];
                if (!results.length) {
                    $main.find("#seed-results").html('<div class="alert alert-info">Nothing to seed (all records already exist).</div>');
                    return;
                }

                const created = results.filter(x => x.action === "created");
                const skipped = results.filter(x => x.action === "skipped");

                let html = `<div class="alert alert-success">${created.length} records created, ${skipped.length} already existed.</div>`;
                html += '<table class="table table-sm"><thead><tr><th>DocType</th><th>Name</th><th>Action</th></tr></thead><tbody>';
                results.forEach(r => {
                    const badge = r.action === "created"
                        ? '<span class="badge badge-success">created</span>'
                        : '<span class="badge badge-secondary">skipped</span>';
                    html += `<tr><td>${r.doctype}</td><td>${r.name}</td><td>${badge}</td></tr>`;
                });
                html += "</tbody></table>";
                $main.find("#seed-results").html(html);
            },
            error: function (r) {
                $btn.prop("disabled", false).html('<i class="fa fa-magic"></i>&nbsp; Seed Demo Data');
                $main.find("#seed-results").html(
                    `<div class="alert alert-danger">Error: ${r.message || "Unknown error"}</div>`
                );
            }
        });
    });
};
