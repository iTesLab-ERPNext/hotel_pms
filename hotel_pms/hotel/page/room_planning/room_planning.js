frappe.pages["room-planning"].on_page_load = function (wrapper) {
	var page = frappe.ui.make_app_page({
		parent: wrapper,
		title: __("Room Planning"),
		single_column: true,
	});

	page.add_button(__("Today"), function () {
		wrapper.room_planning.go_to_today();
	});

	page.add_button(__("← Prev"), function () {
		wrapper.room_planning.go_prev();
	});

	page.add_button(__("Next →"), function () {
		wrapper.room_planning.go_next();
	});

	page.add_button(__("New Reservation"), function () {
		frappe.new_doc("Hotel Reservation");
	}, { icon: "plus" });

	wrapper.room_planning = new RoomPlanning(page);
};

frappe.pages["room-planning"].on_page_show = function (wrapper) {
	if (wrapper.room_planning) {
		wrapper.room_planning.refresh();
	}
};

class RoomPlanning {
	constructor(page) {
		this.page = page;
		this.wrapper = page.body;
		this.from_date = frappe.datetime.get_today();
		this.days = 14;
		this.make();
	}

	make() {
		this.wrapper.html(`
			<div class="room-planning-page" style="padding: 10px; overflow-x: auto;">
				<div id="planning-info" class="mb-2 text-muted" style="font-size: 12px;"></div>
				<div id="planning-board-container">
					<div class="text-center p-4">${__("Loading...")}</div>
				</div>
			</div>
		`);
		this.refresh();
	}

	go_to_today() {
		this.from_date = frappe.datetime.get_today();
		this.refresh();
	}

	go_prev() {
		this.from_date = frappe.datetime.add_days(this.from_date, -this.days);
		this.refresh();
	}

	go_next() {
		this.from_date = frappe.datetime.add_days(this.from_date, this.days);
		this.refresh();
	}

	refresh() {
		frappe.call({
			method: "hotel_pms.hotel.api.get_planning_board",
			args: { from_date: this.from_date, days: this.days },
			callback: (r) => {
				if (r.message) {
					this.data = r.message;
					this.render();
				}
			}
		});
	}

	render() {
		const { rooms, reservations, dates, from_date, to_date } = this.data;

		this.wrapper.find("#planning-info").text(
			__("Showing {0} to {1}", [from_date, to_date])
		);

		if (!rooms || rooms.length === 0) {
			this.wrapper.find("#planning-board-container").html(
				`<div class="alert alert-info">${__("No rooms found. Please create rooms first.")}</div>`
			);
			return;
		}

		// Build reservation lookup: room -> [{reservation, arrival, departure, customer_name, status}]
		const res_by_room = {};
		(reservations || []).forEach(res => {
			if (!res_by_room[res.room]) res_by_room[res.room] = [];
			res_by_room[res.room].push(res);
		});

		// Status colors
		const status_colors = {
			"Confirmed": "#1f6feb",
			"Checked In": "#2da44e",
			"Draft": "#6e7681",
			"Completed": "#8b5cf6",
		};
		const room_status_colors = {
			"Available": "#2da44e",
			"Occupied": "#1f6feb",
			"Reserved": "#fb8500",
			"Cleaning": "#d29922",
			"Maintenance": "#f85149",
			"Blocked": "#6e7681",
			"Out of Service": "#f85149",
		};

		// Build table
		let thead = `<tr><th style="min-width:120px; position:sticky; left:0; background:#fff; z-index:10; border-right: 2px solid #dee2e6;">${__("Room")}</th>`;
		dates.forEach(d => {
			const dt = frappe.datetime.str_to_obj(d);
			const is_today = d === frappe.datetime.get_today();
			const day_name = ["Sun","Mon","Tue","Wed","Thu","Fri","Sat"][dt.getDay()];
			const day_num = dt.getDate();
			thead += `<th style="min-width:38px; text-align:center; font-size:11px; padding:4px; ${is_today ? "background:#fff3cd;" : ""}" title="${d}">
				<div style="font-weight:${is_today ? "bold" : "normal"};">${day_num}</div>
				<div style="color:#6e7681;">${day_name}</div>
			</th>`;
		});
		thead += "</tr>";

		let tbody = "";
		rooms.forEach(room => {
			const room_res = res_by_room[room.name] || [];
			const status_color = room_status_colors[room.status] || "#6e7681";

			tbody += `<tr>
				<td style="position:sticky; left:0; background:#fff; z-index:5; border-right: 2px solid #dee2e6; padding: 4px 8px; white-space:nowrap;">
					<div style="font-weight:600; font-size:13px;">${room.room_number}</div>
					<div style="font-size:11px; color:#6e7681;">${room.room_type || ""}</div>
					<span class="badge" style="background:${status_color}; font-size:9px;">${room.status}</span>
				</td>`;

			dates.forEach(d => {
				// Find reservation on this date
				const res = room_res.find(r => r.arrival_date <= d && r.departure_date > d);
				const is_today = d === frappe.datetime.get_today();
				let cell_bg = is_today ? "#fffbdd" : "#fff";
				let cell_content = "";
				let cell_title = "";
				let cell_data = "";

				if (res) {
					const col = status_colors[res.status] || "#6e7681";
					const is_arrival = res.arrival_date === d;
					const is_departure_prev = frappe.datetime.add_days(res.departure_date, -1) === d;
					cell_bg = col + "22";

					cell_content = `<div style="
						background:${col};
						color:#fff;
						border-radius: ${is_arrival ? "4px 0 0 4px" : (is_departure_prev ? "0 4px 4px 0" : "0")};
						height: 22px;
						font-size:10px;
						overflow:hidden;
						text-overflow:ellipsis;
						white-space:nowrap;
						padding:2px 4px;
						cursor:pointer;
					" class="planning-res-cell" data-reservation="${res.reservation}">
						${is_arrival ? (res.customer_name || res.reservation) : ""}
					</div>`;
					cell_title = `${res.reservation} - ${res.customer_name} (${res.arrival_date} to ${res.departure_date})`;
					cell_data = `data-reservation="${res.reservation}"`;
				}

				tbody += `<td style="padding:2px; background:${cell_bg}; border:1px solid #f0f0f0;" title="${cell_title}" ${cell_data}>${cell_content}</td>`;
			});

			tbody += "</tr>";
		});

		const table_html = `
			<div style="overflow-x: auto;">
				<table class="table table-bordered table-sm planning-table" style="font-size:12px; border-collapse:collapse; min-width: 100%;">
					<thead style="background:#f8f9fa; position:sticky; top:0; z-index:20;">${thead}</thead>
					<tbody>${tbody}</tbody>
				</table>
			</div>
			<div class="mt-2" style="font-size:11px; color:#6e7681;">
				<span class="badge mr-2" style="background:#1f6feb;">Confirmed</span>
				<span class="badge mr-2" style="background:#2da44e;">Checked In</span>
				<span class="badge mr-2" style="background:#6e7681;">Draft</span>
				<span class="badge mr-2" style="background:#8b5cf6;">Completed</span>
			</div>
		`;

		this.wrapper.find("#planning-board-container").html(table_html);

		// Bind click on reservation cells
		this.wrapper.find(".planning-res-cell").on("click", function () {
			const res = $(this).data("reservation");
			if (res) frappe.set_route("Form", "Hotel Reservation", res);
		});
	}
}
