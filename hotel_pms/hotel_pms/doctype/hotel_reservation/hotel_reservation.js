frappe.ui.form.on('Hotel Reservation', {
    refresh: function(frm) {
        frm.trigger('set_custom_buttons');
    },

    set_custom_buttons: function(frm) {
        if (frm.doc.status === 'Confirmed' && !frm.is_new()) {
            frm.add_custom_button(__('Check In'), function() {
                frm.trigger('do_checkin');
            }, __('Actions'));
        }

        if (frm.doc.status === 'Checked In') {
            frm.add_custom_button(__('View Folio'), function() {
                frappe.set_route('List', 'Hotel Folio', {reservation: frm.doc.name});
            }, __('Actions'));
        }
    },

    do_checkin: function(frm) {
        frappe.confirm(
            `Check in customer <b>${frm.doc.customer}</b>?`,
            function() {
                frappe.call({
                    method: 'hotel_pms.api.checkin.checkin',
                    args: {reservation: frm.doc.name},
                    freeze: true,
                    freeze_message: __('Processing Check-in...'),
                    callback: function(r) {
                        if (r.message) {
                            frappe.show_alert({message: __('Check-in successful!'), indicator: 'green'});
                            frm.reload_doc();
                        }
                    }
                });
            }
        );
    },

    arrival_date: function(frm) {
        frm.trigger('calculate_nights');
    },

    departure_date: function(frm) {
        frm.trigger('calculate_nights');
    },

    calculate_nights: function(frm) {
        if (frm.doc.arrival_date && frm.doc.departure_date) {
            let arrival = frappe.datetime.str_to_obj(frm.doc.arrival_date);
            let departure = frappe.datetime.str_to_obj(frm.doc.departure_date);
            let nights = frappe.datetime.get_diff(departure, arrival);
            if (nights > 0) {
                frm.set_value('number_of_nights', nights);
                frm.set_value('number_of_days', nights + 1);
            }
        }
    }
});

frappe.ui.form.on('Hotel Reservation Room', {
    room: function(frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        if (row.room) {
            frappe.db.get_value('Hotel Room', row.room, 'room_type', function(r) {
                if (r) {
                    frappe.model.set_value(cdt, cdn, 'room_type', r.room_type);
                    frappe.db.get_value('Hotel Room Type', r.room_type, 'base_price', function(rt) {
                        if (rt) {
                            frappe.model.set_value(cdt, cdn, 'rate', rt.base_price);
                        }
                    });
                }
            });
        }
    }
});

frappe.ui.form.on('Hotel Reservation Guest', {
    adults: function(frm, cdt, cdn) { update_guest_totals(frm, cdt, cdn); },
    children: function(frm, cdt, cdn) { update_guest_totals(frm, cdt, cdn); },
    infants: function(frm, cdt, cdn) { update_guest_totals(frm, cdt, cdn); }
});

function update_guest_totals(frm, cdt, cdn) {
    let row = locals[cdt][cdn];
    let total = (row.adults || 0) + (row.children || 0) + (row.infants || 0);
    frappe.model.set_value(cdt, cdn, 'total_guests', total);
}
