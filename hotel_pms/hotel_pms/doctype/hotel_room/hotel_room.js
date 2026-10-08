frappe.ui.form.on('Hotel Room', {
    refresh: function(frm) {
        if (!frm.is_new()) {
            frm.add_custom_button(__('Room Calendar'), function() {
                frappe.set_route('hotel-pms-room-planner', {room: frm.doc.name});
            }, __('View'));

            frm.add_custom_button(__('Room Board'), function() {
                frappe.set_route('hotel-pms-room-board');
            }, __('View'));

            if (frm.doc.status === 'Cleaning') {
                frm.add_custom_button(__('Mark Available'), function() {
                    frappe.confirm('Mark this room as Available?', function() {
                        frappe.db.set_value('Hotel Room', frm.doc.name, 'status', 'Available')
                            .then(() => { frm.reload_doc(); });
                    });
                });
            }
        }
    }
});
