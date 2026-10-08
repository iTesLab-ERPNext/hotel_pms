// Hotel Stay form controller
frappe.ui.form.on("Hotel Stay", {
	refresh(frm) {
		frm.trigger("set_status_indicator");
		frm.trigger("add_action_buttons");
	},

	set_status_indicator(frm) {
		const colors = {
			"Active":        "green",
			"Checked Out":   "purple",
			"Late Checkout": "orange",
			"Cancelled":     "red",
		};
		frm.page.set_indicator(frm.doc.status, colors[frm.doc.status] || "gray");
	},

	add_action_buttons(frm) {
		if (frm.is_new()) return;

		if (frm.doc.status === "Active") {
			frm.add_custom_button(__("Check Out"), () => frm.trigger("do_check_out"),
				__("Actions"));
			frm.add_custom_button(__("Move Room"), () => frm.trigger("show_move_room_dialog"),
				__("Actions"));
			frm.add_custom_button(__("Add Charge"), () => frm.trigger("show_add_charge_dialog"),
				__("Actions"));
		}

		if (frm.doc.status === "Active" || frm.doc.status === "Checked Out") {
			frm.add_custom_button(__("View Folio"), () => {
				frappe.xcall("hotel_pms.hotel.api.get_folio_details", { stay: frm.doc.name })
					.then(data => {
						if (!data) {
							frappe.msgprint(__("No folio found for this stay."));
							return;
						}
						frappe.set_route("Form", "Hotel Folio", data.folio.name);
					});
			});
		}
	},

	do_check_out(frm) {
		frappe.confirm(__("Check out {0} from room {1}?", [frm.doc.customer, frm.doc.room]), () => {
			frappe.xcall("hotel_pms.hotel.api.check_out", { stay_name: frm.doc.name })
				.then(r => {
					frappe.show_alert({ message: r.message, indicator: "green" });
					frm.reload_doc();
				});
		});
	},

	show_move_room_dialog(frm) {
		const d = new frappe.ui.Dialog({
			title: __("Move Guest to Different Room"),
			fields: [
				{
					label: __("New Room"),
					fieldname: "new_room",
					fieldtype: "Link",
					options: "Hotel Room",
					filters: { active: 1, status: "Available" },
					reqd: 1,
				},
				{
					label: __("Reason"),
					fieldname: "reason",
					fieldtype: "Select",
					options: ["Guest Request", "Maintenance", "Upgrade", "Downgrade", "Other"].join("\n"),
					default: "Guest Request",
				},
				{
					label: __("New Rate (optional)"),
					fieldname: "new_rate",
					fieldtype: "Currency",
				},
			],
			primary_action_label: __("Move"),
			primary_action({ new_room, reason, new_rate }) {
				frappe.xcall("hotel_pms.hotel.api.move_room", {
					stay_name: frm.doc.name, new_room, reason, new_rate,
				}).then(r => {
					frappe.show_alert({ message: r.message, indicator: "green" });
					frm.reload_doc();
					d.hide();
				});
			},
		});
		d.show();
	},

	show_add_charge_dialog(frm) {
		frappe.xcall("hotel_pms.hotel.api.get_folio_details", { stay: frm.doc.name })
			.then(data => {
				if (!data) {
					frappe.msgprint(__("No open folio for this stay."));
					return;
				}
				const folio = data.folio.name;
				const d = new frappe.ui.Dialog({
					title: __("Add Charge to Folio"),
					fields: [
						{
							label: __("Charge Type"),
							fieldname: "charge_type",
							fieldtype: "Select",
							options: ["Room", "Breakfast", "Lunch", "Dinner", "Spa", "Transport",
								"Laundry", "Extra Bed", "Other"].join("\n"),
							reqd: 1,
						},
						{
							label: __("Description"),
							fieldname: "description",
							fieldtype: "Data",
							reqd: 1,
						},
						{
							label: __("Quantity"),
							fieldname: "quantity",
							fieldtype: "Float",
							default: 1,
							reqd: 1,
						},
						{
							label: __("Rate"),
							fieldname: "rate",
							fieldtype: "Currency",
							reqd: 1,
						},
					],
					primary_action_label: __("Add Charge"),
					primary_action(values) {
						frappe.xcall("hotel_pms.hotel.api.add_folio_charge", {
							folio: folio,
							...values,
						}).then(() => {
							frappe.show_alert({ message: __("Charge added"), indicator: "green" });
							d.hide();
						});
					},
				});
				d.show();
			});
	},
});
