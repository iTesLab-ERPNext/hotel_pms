frappe.ui.form.on('Hotel Stay', {
    refresh(frm) {
        if (frm.doc.status === 'Checked In') {
            frm.add_custom_button(__('Check Out'), () => {
                frappe.call({
                    method: 'hotel_pms.hotel_pms.api.checkout.get_checkout_summary',
                    args: { stay_name: frm.doc.name },
                    callback(r) {
                        const s = r.message;
                        const balance = s.balance || 0;
                        let msg = `<b>Balance due: ${format_currency(balance)}</b>`;
                        frappe.confirm(msg + '<br>Proceed with checkout?', () => {
                            frappe.call({
                                method: 'hotel_pms.hotel_pms.api.checkout.checkout_stay',
                                args: { stay_name: frm.doc.name, force: balance <= 0 ? 1 : 0 },
                                callback(r2) {
                                    frappe.show_alert({message: 'Checked out successfully', indicator: 'green'});
                                    frm.reload_doc();
                                }
                            });
                        });
                    }
                });
            }, __('Actions'));

            frm.add_custom_button(__('Add Charge'), () => {
                frappe.prompt([
                    {label: 'Folio', fieldtype: 'Link', options: 'Hotel Folio', fieldname: 'folio_name', reqd: 1,
                     get_query: () => ({filters: {stay: frm.doc.name}})},
                    {label: 'Charge Type', fieldtype: 'Select', options: 'F&B\nLaundry\nTransport\nSpa\nParking\nRecreation\nMiscellaneous', fieldname: 'charge_type', reqd: 1},
                    {label: 'Description', fieldtype: 'Data', fieldname: 'description', reqd: 1},
                    {label: 'Amount', fieldtype: 'Currency', fieldname: 'amount', reqd: 1},
                    {label: 'Qty', fieldtype: 'Int', fieldname: 'qty', default: 1}
                ], (vals) => {
                    frappe.call({
                        method: 'hotel_pms.hotel_pms.api.folio.add_charge',
                        args: {folio_name: vals.folio_name, charge_type: vals.charge_type, description: vals.description, amount: vals.amount, qty: vals.qty},
                        callback(r) { frappe.show_alert({message: 'Charge added', indicator: 'green'}); }
                    });
                });
            }, __('Actions'));

            frm.add_custom_button(__('Post Payment'), () => {
                frappe.prompt([
                    {label: 'Folio', fieldtype: 'Link', options: 'Hotel Folio', fieldname: 'folio_name', reqd: 1,
                     get_query: () => ({filters: {stay: frm.doc.name}})},
                    {label: 'Payment Method', fieldtype: 'Select', options: 'Cash\nCredit Card\nDebit Card\nBank Transfer', fieldname: 'payment_method', reqd: 1},
                    {label: 'Amount', fieldtype: 'Currency', fieldname: 'amount', reqd: 1}
                ], (vals) => {
                    frappe.call({
                        method: 'hotel_pms.hotel_pms.api.payment.post_payment',
                        args: {folio_name: vals.folio_name, payment_method: vals.payment_method, amount: vals.amount},
                        callback(r) { frappe.show_alert({message: 'Payment posted', indicator: 'green'}); }
                    });
                });
            }, __('Actions'));
        }
    }
});

function format_currency(val) {
    return frappe.format(val, {fieldtype: 'Currency'});
}
