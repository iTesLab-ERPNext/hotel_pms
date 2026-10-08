frappe.pages['hotel-pms-room-planner'].on_page_load = function(wrapper) {
    var page = frappe.ui.make_app_page({
        parent: wrapper,
        title: 'Room Planner',
        single_column: true
    });
    page.main.html(`<div id="room-planner-container"></div>`);
    frappe.require(['/assets/hotel_pms/js/hotel_pms.js'], function() {
        hotel_pms.room_planner.init(page);
    });
};
