frappe.pages['hotel-pms-test-data'].on_page_load = function(wrapper) {
    var page = frappe.ui.make_app_page({
        parent: wrapper,
        title: 'Hotel PMS Test Data',
        single_column: true
    });

    frappe.require(['/assets/hotel_pms/js/hotel_pms.js'], function() {
        hotel_pms.test_data.init(page);
    });
};
