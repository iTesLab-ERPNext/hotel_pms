frappe.ui.form.on('Hotel Folio', {
    refresh: function(frm) {
        if (frm.doc.status === 'Open' && !frm.is_new()) {
            frm.add_custom_button(__('Add Payment'), function() {
                frappe.new_doc('Hotel Payment', {folio: frm.doc.name, customer: frm.doc.customer});
            });
        }
    }
});

frappe.ui.form.on('Hotel Folio Item', {
    quantity: function(frm, cdt, cdn) { calc_item_amount(frm, cdt, cdn); },
    rate: function(frm, cdt, cdn) { calc_item_amount(frm, cdt, cdn); },
    service: function(frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        if (row.service) {
            frappe.db.get_value('Hotel Service', row.service, ['rate', 'service_name'], function(r) {
                if (r) {
                    frappe.model.set_value(cdt, cdn, 'rate', r.rate);
                    frappe.model.set_value(cdt, cdn, 'description', r.service_name);
                }
            });
        }
        calc_item_amount(frm, cdt, cdn);
    }
});

function calc_item_amount(frm, cdt, cdn) {
    let row = locals[cdt][cdn];
    frappe.model.set_value(cdt, cdn, 'amount', (row.quantity || 1) * (row.rate || 0));
    frm.trigger('recalculate_totals');
}
