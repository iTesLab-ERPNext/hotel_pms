frappe.ui.form.on("Hotel Reservation", {
    refresh(frm) {
        if (frm.doc.reservation_status === "Draft") {
            frm.add_custom_button(__("Confirm"), () => {
                frappe.call({
                    method: "hotel_pms.api.reservation.confirm_reservation",
                    args: { reservation_name: frm.doc.name },
                    callback(r) { frm.reload_doc(); }
                });
            }, __("Actions"));
        }

        if (["Confirmed", "Deposit Paid"].includes(frm.doc.reservation_status)) {
            frm.add_custom_button(__("Check In"), () => {
                frappe.call({
                    method: "hotel_pms.api.checkin.checkin_from_reservation",
                    args: { reservation_name: frm.doc.name },
                    callback(r) {
                        if (r.message) {
                            frappe.msgprint(`Stay <b>${r.message.stay}</b> created. Folio: <b>${r.message.folio}</b>`);
                            frm.reload_doc();
                        }
                    }
                });
            }, __("Actions"));

            frm.add_custom_button(__("Cancel"), () => {
                frappe.prompt([
                    { label: "Reason", fieldname: "reason", fieldtype: "Small Text", reqd: 1 },
                    { label: "Cancellation Charge", fieldname: "charge", fieldtype: "Currency" }
                ], (vals) => {
                    frappe.call({
                        method: "hotel_pms.api.reservation.cancel_reservation",
                        args: { reservation_name: frm.doc.name, reason: vals.reason, charge: vals.charge || 0 },
                        callback(r) { frm.reload_doc(); }
                    });
                }, __("Cancel Reservation"));
            }, __("Actions"));
        }
    },

    arrival_date(frm) { frm.trigger("calc_nights"); },
    departure_date(frm) { frm.trigger("calc_nights"); },

    calc_nights(frm) {
        if (frm.doc.arrival_date && frm.doc.departure_date) {
            const ci = frappe.datetime.str_to_obj(frm.doc.arrival_date);
            const co = frappe.datetime.str_to_obj(frm.doc.departure_date);
            const nights = (co - ci) / 86400000;
            frm.set_value("number_of_nights", Math.max(0, Math.round(nights)));
        }
    }
});
