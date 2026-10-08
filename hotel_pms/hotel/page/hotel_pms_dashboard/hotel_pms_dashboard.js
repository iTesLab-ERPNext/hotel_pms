frappe.pages["hotel-pms-dashboard"].on_page_load = function (wrapper) {
	var page = frappe.ui.make_app_page({
		parent: wrapper,
		title: __("Hotel PMS Dashboard"),
		single_column: true,
	});

	page.add_button(__("Refresh"), function () {
		hotel_dashboard.refresh();
	}, { icon: "refresh" });

	page.add_button(__("New Reservation"), function () {
		frappe.new_doc("Hotel Reservation");
	}, { icon: "plus" });

	page.add_button(__("Room Planning"), function () {
		frappe.set_route("room-planning");
	}, { icon: "calendar" });

	wrapper.hotel_dashboard = new HotelDashboard(page);
};

frappe.pages["hotel-pms-dashboard"].on_page_show = function (wrapper) {
	if (wrapper.hotel_dashboard) {
		wrapper.hotel_dashboard.refresh();
	}
};

class HotelDashboard {
	constructor(page) {
		this.page = page;
		this.wrapper = page.body;
		this.make();
	}

	make() {
		this.wrapper.html(`
			<div class="hotel-dashboard" style="padding: 15px;">
				<div id="dashboard-loading" class="text-center" style="padding: 40px;">
					<div class="spinner-border text-primary" role="status">
						<span class="sr-only">Loading...</span>
					</div>
					<p class="mt-2">${__("Loading dashboard...")}</p>
				</div>
				<div id="dashboard-content" style="display:none;">
					<!-- Today's Operations -->
					<div class="row mb-3">
						<div class="col-12">
							<h5 class="text-muted text-uppercase" style="font-size: 11px; letter-spacing: 1px;">
								${__("Today's Operations")}
							</h5>
						</div>
					</div>
					<div class="row mb-4" id="today-cards"></div>

					<!-- Room Status -->
					<div class="row mb-3">
						<div class="col-12">
							<h5 class="text-muted text-uppercase" style="font-size: 11px; letter-spacing: 1px;">
								${__("Room Status")}
							</h5>
						</div>
					</div>
					<div class="row mb-4" id="room-cards"></div>

					<!-- Reservations -->
					<div class="row mb-3">
						<div class="col-12">
							<h5 class="text-muted text-uppercase" style="font-size: 11px; letter-spacing: 1px;">
								${__("Reservations")}
							</h5>
						</div>
					</div>
					<div class="row mb-4" id="reservation-cards"></div>

					<!-- Financial -->
					<div class="row mb-3">
						<div class="col-12">
							<h5 class="text-muted text-uppercase" style="font-size: 11px; letter-spacing: 1px;">
								${__("Financial")}
							</h5>
						</div>
					</div>
					<div class="row mb-4" id="financial-cards"></div>

					<!-- Quick Actions -->
					<div class="row mb-3">
						<div class="col-12">
							<h5 class="text-muted text-uppercase" style="font-size: 11px; letter-spacing: 1px;">
								${__("Quick Actions")}
							</h5>
						</div>
					</div>
					<div class="row" id="quick-actions"></div>
				</div>
			</div>
		`);

		this.refresh();
	}

	refresh() {
		frappe.call({
			method: "hotel_pms.api.hotel_api.get_dashboard_data",
			callback: (r) => {
				if (r.message) {
					this.render(r.message);
				}
			},
			error: () => {
				this.wrapper.find("#dashboard-loading").html(
					`<div class="alert alert-danger">${__("Failed to load dashboard data")}</div>`
				);
			}
		});
	}

	render(data) {
		this.wrapper.find("#dashboard-loading").hide();
		this.wrapper.find("#dashboard-content").show();

		this.renderTodayCards(data.today);
		this.renderRoomCards(data.rooms);
		this.renderReservationCards(data.reservations);
		this.renderFinancialCards(data.financial);
		this.renderQuickActions();
	}

	renderTodayCards(today) {
		const cards = [
			{ label: __("Today Arrivals"), value: today.arrivals, icon: "fa fa-plane-arrival", color: "blue", route: ["List", "Hotel Reservation", {arrival_date: frappe.datetime.get_today(), status: ["in", ["Confirmed", "Checked In"]]}] },
			{ label: __("Today Departures"), value: today.departures, icon: "fa fa-plane-departure", color: "orange", route: ["List", "Hotel Reservation", {departure_date: frappe.datetime.get_today(), status: "Checked In"}] },
			{ label: __("Active Stays"), value: today.active_stays, icon: "fa fa-bed", color: "green", route: ["List", "Hotel Stay", {status: "Active"}] },
			{ label: __("Available Rooms"), value: today.available_rooms, icon: "fa fa-door-open", color: "teal", route: ["List", "Hotel Room", {status: "Available"}] },
		];
		this.wrapper.find("#today-cards").html(cards.map(c => this.makeStatCard(c)).join(""));
		this.bindCardClicks(this.wrapper.find("#today-cards"), cards);
	}

	renderRoomCards(rooms) {
		const cards = [
			{ label: __("Total Rooms"), value: rooms.total, icon: "fa fa-building", color: "gray" },
			{ label: __("Available"), value: rooms.available, icon: "fa fa-check-circle", color: "green" },
			{ label: __("Occupied"), value: rooms.occupied, icon: "fa fa-user", color: "blue" },
			{ label: __("Reserved"), value: rooms.reserved, icon: "fa fa-bookmark", color: "purple" },
			{ label: __("Cleaning"), value: rooms.cleaning, icon: "fa fa-broom", color: "yellow" },
			{ label: __("Maintenance"), value: rooms.maintenance, icon: "fa fa-tools", color: "red" },
		];
		this.wrapper.find("#room-cards").html(cards.map(c => this.makeStatCard(c)).join(""));
	}

	renderReservationCards(res) {
		const cards = [
			{ label: __("Draft"), value: res.draft, icon: "fa fa-file", color: "gray" },
			{ label: __("Confirmed"), value: res.confirmed, icon: "fa fa-check", color: "blue" },
			{ label: __("Checked In"), value: res.checked_in, icon: "fa fa-sign-in-alt", color: "green" },
			{ label: __("Completed"), value: res.completed, icon: "fa fa-flag-checkered", color: "teal" },
			{ label: __("Cancelled"), value: res.cancelled, icon: "fa fa-times-circle", color: "red" },
			{ label: __("No Show"), value: res.no_show, icon: "fa fa-ghost", color: "orange" },
		];
		this.wrapper.find("#reservation-cards").html(cards.map(c => this.makeStatCard(c)).join(""));
	}

	renderFinancialCards(fin) {
		const cards = [
			{
				label: __("Today's Collections"),
				value: format_currency(fin.today_payments || 0),
				icon: "fa fa-cash-register",
				color: "green",
				is_currency: true
			},
			{
				label: __("Outstanding Balance"),
				value: format_currency(fin.outstanding_balances || 0),
				icon: "fa fa-exclamation-circle",
				color: fin.outstanding_balances > 0 ? "red" : "gray",
				is_currency: true
			},
		];
		this.wrapper.find("#financial-cards").html(cards.map(c => this.makeStatCard(c)).join(""));
	}

	renderQuickActions() {
		const actions = [
			{ label: __("New Reservation"), icon: "fa fa-plus", fn: () => frappe.new_doc("Hotel Reservation"), color: "primary" },
			{ label: __("New Customer"), icon: "fa fa-user-plus", fn: () => frappe.new_doc("Hotel Customer"), color: "secondary" },
			{ label: __("Room Planning"), icon: "fa fa-calendar-alt", fn: () => frappe.set_route("room-planning"), color: "info" },
			{ label: __("Housekeeping"), icon: "fa fa-broom", fn: () => frappe.set_route("List", "Hotel Housekeeping"), color: "warning" },
			{ label: __("Payments"), icon: "fa fa-money-bill-wave", fn: () => frappe.set_route("List", "Hotel Payment"), color: "success" },
			{ label: __("Folios"), icon: "fa fa-file-invoice-dollar", fn: () => frappe.set_route("List", "Hotel Folio"), color: "secondary" },
		];

		const html = actions.map(a => `
			<div class="col-md-2 col-sm-4 mb-3">
				<button class="btn btn-${a.color} btn-block quick-action-btn" style="white-space:normal;">
					<i class="${a.icon} mr-1"></i> ${a.label}
				</button>
			</div>
		`).join("");

		this.wrapper.find("#quick-actions").html(html);

		actions.forEach((a, i) => {
			this.wrapper.find(".quick-action-btn").eq(i).on("click", a.fn);
		});
	}

	makeStatCard(c) {
		const color_map = {
			blue: "#1f6feb", green: "#2da44e", red: "#f85149",
			orange: "#fb8500", teal: "#2ea8a8", purple: "#8b5cf6",
			yellow: "#d29922", gray: "#6e7681", primary: "#1f6feb"
		};
		const color = color_map[c.color] || "#6e7681";
		return `
			<div class="col-md-2 col-sm-4 mb-3 dashboard-stat-card" data-route='${JSON.stringify(c.route || null)}'>
				<div class="card h-100" style="border-left: 4px solid ${color}; cursor: ${c.route ? "pointer" : "default"};">
					<div class="card-body p-3">
						<div class="d-flex justify-content-between align-items-start">
							<div>
								<div style="font-size: 24px; font-weight: 700; color: ${color};">${c.value}</div>
								<div class="text-muted" style="font-size: 12px;">${c.label}</div>
							</div>
							<i class="${c.icon}" style="color: ${color}; opacity: 0.3; font-size: 28px;"></i>
						</div>
					</div>
				</div>
			</div>
		`;
	}

	bindCardClicks(container, cards) {
		container.find(".dashboard-stat-card").each(function (i) {
			const route = cards[i] && cards[i].route;
			if (route) {
				$(this).on("click", function () {
					frappe.set_route(...route);
				});
			}
		});
	}
}
