frappe.pages['hotel-pms-room-board'].on_page_load = function(wrapper) {
    var page = frappe.ui.make_app_page({
        parent: wrapper,
        title: 'Room Board',
        single_column: true
    });

    page.set_secondary_action('Refresh', () => hotel_pms.room_board.load(), 'refresh');

    page.main.html(`<div id="room-board-container"></div>`);
    frappe.require(['/assets/hotel_pms/js/hotel_pms.js'], function() {
        hotel_pms.room_board.init(page);
    });
};
