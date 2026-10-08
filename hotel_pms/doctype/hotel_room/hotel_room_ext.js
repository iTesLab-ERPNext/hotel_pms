frappe.ui.form.on("Hotel Room", {
    refresh(frm) {
        frm.add_custom_button(__("Room Board"), () => {
            frappe.set_route("room-board");
        });

        if (!frm.doc.__islocal) {
            frm.add_custom_button(__("Mark Available"), () => {
                frappe.call({
                    method: "frappe.client.set_value",
                    args: { doctype: "Hotel Room", name: frm.doc.name, fieldname: "status", value: "Available" },
                    callback() { frm.reload_doc(); }
                });
            }, __("Status"));

            frm.add_custom_button(__("Mark Dirty"), () => {
                frappe.call({
                    method: "frappe.client.set_value",
                    args: { doctype: "Hotel Room", name: frm.doc.name, fieldname: "status", value: "Dirty" },
                    callback() { frm.reload_doc(); }
                });
            }, __("Status"));

            frm.add_custom_button(__("Mark Maintenance"), () => {
                frappe.call({
                    method: "frappe.client.set_value",
                    args: { doctype: "Hotel Room", name: frm.doc.name, fieldname: "status", value: "Maintenance" },
                    callback() { frm.reload_doc(); }
                });
            }, __("Status"));
        }
    }
});
