frappe.ui.form.on('Hotel Stay', {
    refresh: function(frm) {
        if (frm.doc.status === 'Active') {
            frm.add_custom_button(__('Checkout'), function() {
                frappe.confirm('Proceed with checkout?', function() {
                    frappe.call({
                        method: 'hotel_pms.api.checkout.checkout',
                        args: {stay: frm.doc.name},
                        freeze: true,
                        callback: function(r) {
                            if (r.message && r.message.success) {
                                frappe.show_alert({message: 'Checkout successful!', indicator: 'green'});
                                frm.reload_doc();
                            }
                        }
                    });
                });
            });

            frm.add_custom_button(__('Move Room'), function() {
                frappe.set_route('new-hotel-room-movement', {stay: frm.doc.name});
            });

            frm.add_custom_button(__('Add Charge'), function() {
                let folio = frappe.db.get_value('Hotel Folio', {stay: frm.doc.name}, 'name');
                if (folio) {
                    frappe.set_route('Form', 'Hotel Folio', folio.name);
                }
            });
        }
    }
});
