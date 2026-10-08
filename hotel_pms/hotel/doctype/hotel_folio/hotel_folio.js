// Hotel Folio form controller
frappe.ui.form.on("Hotel Folio", {
	refresh(frm) {
		frm.trigger("set_status_indicator");
		frm.trigger("add_action_buttons");
	},

	set_status_indicator(frm) {
		const colors = {
			"Open":           "blue",
			"Partially Paid": "orange",
			"Paid":           "green",
			"Closed":         "gray",
		};
		frm.page.set_indicator(frm.doc.status, colors[frm.doc.status] || "gray");
	},

	add_action_buttons(frm) {
		if (frm.is_new()) return;

		if (frm.doc.status !== "Closed") {
			frm.add_custom_button(__("Add Charge"), () => {
				frm.trigger("show_add_charge_dialog");
			}, __("Actions"));

			frm.add_custom_button(__("Receive Payment"), () => {
				frm.trigger("show_payment_dialog");
			}, __("Actions"));

			frm.add_custom_button(__("Refresh Balance"), () => {
				frm.call("refresh_balance").then(() => frm.reload_doc());
			}, __("Actions"));
		}
	},

	show_add_charge_dialog(frm) {
		const d = new frappe.ui.Dialog({
			title: __("Add Charge"),
			fields: [
				{
					label: __("Charge Type"),
					fieldname: "charge_type",
					fieldtype: "Select",
					options: ["Room", "Breakfast", "Lunch", "Dinner", "Spa",
						"Transport", "Laundry", "Extra Bed", "Other"].join("\n"),
					reqd: 1,
				},
				{
					label: __("Description"),
					fieldname: "description",
					fieldtype: "Data",
					reqd: 1,
				},
				{ label: __("Quantity"), fieldname: "quantity", fieldtype: "Float", default: 1, reqd: 1 },
				{ label: __("Rate"), fieldname: "rate", fieldtype: "Currency", reqd: 1 },
			],
			primary_action_label: __("Add"),
			primary_action(values) {
				frappe.xcall("hotel_pms.hotel.api.add_folio_charge", {
					folio: frm.doc.name, ...values,
				}).then(() => {
					frappe.show_alert({ message: __("Charge added"), indicator: "green" });
					frm.reload_doc();
					d.hide();
				});
			},
		});
		d.show();
	},

	show_payment_dialog(frm) {
		const balance = frm.doc.balance || 0;
		const d = new frappe.ui.Dialog({
			title: __("Receive Payment"),
			fields: [
				{
					label: __("Payment Method"),
					fieldname: "payment_method",
					fieldtype: "Select",
					options: ["Cash", "Card", "Bank Transfer", "Cheque", "Online", "Other"].join("\n"),
					default: "Cash",
					reqd: 1,
				},
				{
					label: __("Amount"),
					fieldname: "amount",
					fieldtype: "Currency",
					default: balance,
					reqd: 1,
				},
				{
					label: __("Payment Type"),
					fieldname: "payment_type",
					fieldtype: "Select",
					options: ["Partial", "Full", "Advance", "Refund"].join("\n"),
					default: balance > 0 ? "Full" : "Partial",
				},
				{ label: __("Reference"), fieldname: "reference", fieldtype: "Data" },
			],
			primary_action_label: __("Receive"),
			primary_action({ payment_method, amount, payment_type, reference }) {
				frappe.xcall("hotel_pms.hotel.api.create_payment", {
					customer:        frm.doc.customer,
					amount:          amount,
					payment_method:  payment_method,
					payment_type:    payment_type,
					reservation:     frm.doc.reservation,
					stay:            frm.doc.stay,
					folio:           frm.doc.name,
					reference:       reference,
				}).then(() => {
					frappe.show_alert({ message: __("Payment received"), indicator: "green" });
					frm.reload_doc();
					d.hide();
				});
			},
		});
		d.show();
	},
});
