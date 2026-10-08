frappe.pages['hotel-dashboard'].on_page_load = function(wrapper) {
    var page = frappe.ui.make_app_page({
        parent: wrapper,
        title: 'Hotel Dashboard',
        single_column: true
    });

    page.main.html(`
        <div id="hotel-dashboard" class="hotel-pms-dashboard">
            <div class="loading-state text-center py-5">
                <div class="spinner-border text-primary" role="status"></div>
                <p class="mt-2 text-muted">Loading dashboard...</p>
            </div>
        </div>
    `);

    frappe.require(['/assets/hotel_pms/js/hotel_pms.js'], function() {
        hotel_pms.dashboard.init(page);
    });
};

frappe.pages['hotel-dashboard'].on_page_show = function(wrapper) {
    hotel_pms.dashboard && hotel_pms.dashboard.refresh();
};
