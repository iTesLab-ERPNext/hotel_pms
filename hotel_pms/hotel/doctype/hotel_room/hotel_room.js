// Hotel Room form controller
frappe.ui.form.on("Hotel Room", {
	refresh(frm) {
		frm.trigger("set_status_indicator");
		frm.trigger("add_action_buttons");
	},

	set_status_indicator(frm) {
		const colors = {
			"Available":      "green",
			"Occupied":       "blue",
			"Reserved":       "yellow",
			"Cleaning":       "orange",
			"Maintenance":    "red",
			"Blocked":        "gray",
			"Out of Service": "darkgray",
		};
		frm.page.set_indicator(frm.doc.status, colors[frm.doc.status] || "gray");
	},

	add_action_buttons(frm) {
		if (frm.is_new()) return;

		if (frm.doc.status !== "Available") {
			frm.add_custom_button(__("Set Available"), () => {
				frm.call("set_available").then(() => frm.reload_doc());
			}, __("Status"));
		}

		if (frm.doc.status !== "Maintenance") {
			frm.add_custom_button(__("Set Maintenance"), () => {
				frm.call("set_maintenance").then(() => frm.reload_doc());
			}, __("Status"));
		}

		frm.add_custom_button(__("Update Housekeeping"), () => {
			frm.trigger("show_housekeeping_dialog");
		}, __("Actions"));

		frm.add_custom_button(__("Active Stays"), () => {
			frappe.set_route("List", "Hotel Stay", { room: frm.doc.name, status: "Active" });
		});
	},

	show_housekeeping_dialog(frm) {
		const d = new frappe.ui.Dialog({
			title: __("Update Housekeeping Status"),
			fields: [
				{
					label: __("New Status"),
					fieldname: "new_status",
					fieldtype: "Select",
					options: ["Clean", "Dirty", "Inspected", "In Progress"].join("\n"),
					reqd: 1,
				},
				{
					label: __("Notes"),
					fieldname: "notes",
					fieldtype: "Small Text",
				},
			],
			primary_action_label: __("Update"),
			primary_action({ new_status, notes }) {
				frappe.xcall("hotel_pms.hotel.api.update_housekeeping_status", {
					room: frm.doc.name, new_status, notes,
				}).then(() => {
					frappe.show_alert({ message: __("Housekeeping status updated"), indicator: "green" });
					frm.reload_doc();
					d.hide();
				});
			},
		});
		d.show();
	},
});
