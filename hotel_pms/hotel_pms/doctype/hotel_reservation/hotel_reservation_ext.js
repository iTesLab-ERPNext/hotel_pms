frappe.ui.form.on('Hotel Reservation', {
    arrival_date(frm) { calc_nights(frm); },
    departure_date(frm) { calc_nights(frm); },
    refresh(frm) {
        if (!frm.is_new()) {
            if (frm.doc.status === 'Pending' || frm.doc.status === 'Tentative') {
                frm.add_custom_button(__('Confirm'), () => {
                    frappe.call({
                        method: 'hotel_pms.hotel_pms.api.reservation.confirm_reservation',
                        args: { reservation_name: frm.doc.name },
                        callback(r) { frm.reload_doc(); }
                    });
                }, __('Actions'));
            }
            if (frm.doc.status === 'Confirmed') {
                frm.add_custom_button(__('Check In'), () => {
                    frappe.call({
                        method: 'hotel_pms.hotel_pms.api.checkin.checkin_from_reservation',
                        args: { reservation_name: frm.doc.name },
                        callback(r) {
                            frappe.show_alert({message: `Checked in. Stay: ${r.message.stay}`, indicator: 'green'});
                            frm.reload_doc();
                        }
                    });
                }, __('Actions'));
            }
            if (!['Cancelled', 'Checked In', 'Checked Out'].includes(frm.doc.status)) {
                frm.add_custom_button(__('Cancel'), () => {
                    frappe.prompt({label: 'Reason', fieldtype: 'Small Text'}, (vals) => {
                        frappe.call({
                            method: 'hotel_pms.hotel_pms.api.reservation.cancel_reservation',
                            args: { reservation_name: frm.doc.name, reason: vals.value },
                            callback(r) { frm.reload_doc(); }
                        });
                    });
                }, __('Actions'));
            }
        }
    }
});

function calc_nights(frm) {
    if (frm.doc.arrival_date && frm.doc.departure_date) {
        const a = frappe.datetime.str_to_obj(frm.doc.arrival_date);
        const d = frappe.datetime.str_to_obj(frm.doc.departure_date);
        const nights = Math.round((d - a) / 86400000);
        frm.set_value('number_of_nights', nights > 0 ? nights : 0);
    }
}
