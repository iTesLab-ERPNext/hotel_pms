// Hotel Reservation form controller
frappe.ui.form.on("Hotel Reservation", {
	setup(frm) {
		frm.set_query("room", "rooms", () => ({ filters: { active: 1 } }));
		frm.set_query("customer", () => ({ filters: { active: 1 } }));
	},

	refresh(frm) {
		frm.trigger("set_status_indicator");
		frm.trigger("add_action_buttons");
	},

	set_status_indicator(frm) {
		const colors = {
			"Draft":      "gray",
			"Confirmed":  "blue",
			"Checked In": "green",
			"Completed":  "purple",
			"Cancelled":  "red",
			"No Show":    "orange",
		};
		frm.page.set_indicator(frm.doc.status, colors[frm.doc.status] || "gray");
	},

	add_action_buttons(frm) {
		if (frm.is_new()) return;

		if (frm.doc.status === "Confirmed") {
			frm.add_custom_button(__("Check In"), () => frm.trigger("do_check_in"),
				__("Actions"));
			frm.add_custom_button(__("Mark No Show"), () => frm.trigger("do_no_show"),
				__("Actions"));
			frm.add_custom_button(__("Cancel"), () => frm.trigger("do_cancel"),
				__("Actions"));
		}

		if (frm.doc.status === "Draft") {
			frm.add_custom_button(__("Confirm"), () => {
				frappe.confirm(__("Confirm this reservation?"), () => {
					frappe.db.set_value("Hotel Reservation", frm.doc.name, "status", "Confirmed")
						.then(() => frm.reload_doc());
				});
			}, __("Actions"));
		}

		if (["Confirmed", "Checked In"].includes(frm.doc.status)) {
			frm.add_custom_button(__("Check Availability"), () => frm.trigger("show_availability"),
				__("Tools"));
		}
	},

	arrival_date(frm) { frm.trigger("calculate_nights"); },
	departure_date(frm) { frm.trigger("calculate_nights"); },

	calculate_nights(frm) {
		if (frm.doc.arrival_date && frm.doc.departure_date) {
			const a = frappe.datetime.str_to_obj(frm.doc.arrival_date);
			const d = frappe.datetime.str_to_obj(frm.doc.departure_date);
			const nights = frappe.datetime.get_diff(d, a);
			frm.set_value("number_of_nights", nights > 0 ? nights : 0);
		}
	},

	do_check_in(frm) {
		frappe.confirm(
			__("Check in reservation {0}?", [frm.doc.name]),
			() => {
				frappe.xcall("hotel_pms.hotel.api.check_in", { reservation: frm.doc.name })
					.then(r => {
						frappe.show_alert({ message: r.message, indicator: "green" });
						frm.reload_doc();
					});
			}
		);
	},

	do_cancel(frm) {
		frappe.prompt(
			{ label: __("Reason"), fieldname: "reason", fieldtype: "Small Text" },
			({ reason }) => {
				frm.call("cancel_reservation", { reason }).then(() => frm.reload_doc());
			},
			__("Cancel Reservation")
		);
	},

	do_no_show(frm) {
		frappe.confirm(__("Mark as No Show?"), () => {
			frm.call("mark_no_show").then(() => frm.reload_doc());
		});
	},

	show_availability(frm) {
		if (!frm.doc.arrival_date || !frm.doc.departure_date) {
			frappe.msgprint(__("Set arrival and departure dates first."));
			return;
		}
		frappe.xcall("hotel_pms.hotel.api.get_room_availability", {
			arrival_date:   frm.doc.arrival_date,
			departure_date: frm.doc.departure_date,
		}).then(rooms => {
			const lines = rooms.length
				? rooms.map(r => `<b>${r.room_number}</b> — ${r.room_type} (cap. ${r.capacity})`).join("<br>")
				: __("No rooms available for these dates.");
			frappe.msgprint({ title: __("Available Rooms"), message: lines });
		});
	},
});

// Child table: rooms
frappe.ui.form.on("Hotel Reservation Room", {
	room(frm, cdt, cdn) {
		const row = locals[cdt][cdn];
		if (row.room) {
			frappe.db.get_value("Hotel Room", row.room, ["room_type", "rate", "capacity"])
				.then(({ message: v }) => {
					frappe.model.set_value(cdt, cdn, "room_type", v.room_type);
					if (!row.rate) frappe.model.set_value(cdt, cdn, "rate", v.rate || 0);
				});
		}
	},
	rate(frm) { frm.trigger("refresh_room_totals"); },
	nights(frm) { frm.trigger("refresh_room_totals"); },
	refresh_room_totals(frm, cdt, cdn) {
		const row = locals[cdt][cdn];
		const nights = row.nights || frm.doc.number_of_nights || 0;
		frappe.model.set_value(cdt, cdn, "amount", (row.rate || 0) * nights);
	},
});
