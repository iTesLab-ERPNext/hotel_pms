frappe.ui.form.on('Hotel Housekeeping', {
    refresh: function(frm) {
        if (frm.doc.status === 'Dirty') {
            frm.add_custom_button(__('Start Cleaning'), function() {
                frm.set_value('status', 'Cleaning');
                frm.save();
            });
        }
        if (frm.doc.status === 'Cleaning') {
            frm.add_custom_button(__('Mark Clean'), function() {
                frm.set_value('status', 'Clean');
                frm.save();
            });
        }
        if (frm.doc.status === 'Clean') {
            frm.add_custom_button(__('Inspect & Approve'), function() {
                frm.set_value('status', 'Inspected');
                frm.save();
            });
        }
    }
});
