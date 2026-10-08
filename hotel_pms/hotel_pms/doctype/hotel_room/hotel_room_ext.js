frappe.ui.form.on('Hotel Room', {
    refresh(frm) {
        if (frm.doc.status === 'Dirty') {
            frm.add_custom_button(__('Mark Available'), () => {
                frappe.db.set_value('Hotel Room', frm.doc.name, 'status', 'Available')
                    .then(() => { frm.reload_doc(); frappe.show_alert({message: 'Room marked Available', indicator: 'green'}); });
            }, __('Actions'));
        }
        if (frm.doc.status === 'Available') {
            frm.add_custom_button(__('Mark Dirty'), () => {
                frappe.db.set_value('Hotel Room', frm.doc.name, 'status', 'Dirty')
                    .then(() => { frm.reload_doc(); });
            }, __('Actions'));
            frm.add_custom_button(__('Mark Maintenance'), () => {
                frappe.db.set_value('Hotel Room', frm.doc.name, 'status', 'Maintenance')
                    .then(() => { frm.reload_doc(); });
            }, __('Actions'));
        }
    }
});
