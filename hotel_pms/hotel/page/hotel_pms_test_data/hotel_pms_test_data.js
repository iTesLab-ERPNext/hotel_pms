frappe.pages["hotel-pms-test-data"].on_page_load = function (wrapper) {
	var page = frappe.ui.make_app_page({
		parent: wrapper,
		title: __("Hotel PMS Test Data"),
		single_column: true,
	});

	wrapper.test_data_page = new HotelTestDataPage(page);
};

class HotelTestDataPage {
	constructor(page) {
		this.page = page;
		this.wrapper = page.body;
		this.make();
	}

	make() {
		this.wrapper.html(`
			<div style="max-width: 700px; margin: 40px auto; padding: 0 15px;">
				<div class="card">
					<div class="card-body">
						<h4 class="card-title">${__("Test Data Manager")}</h4>
						<p class="text-muted">
							${__("Use this page to load demo data for testing the Hotel PMS. Test data records are marked with 'Is Test Data' and can be safely deleted without affecting production data.")}
						</p>
						<hr>

						<div class="mb-4">
							<h6>${__("What gets created:")}</h6>
							<ul class="text-muted" style="font-size: 13px;">
								<li>${__("4 Room Types (Standard, Deluxe, Suite, Family)")} </li>
								<li>${__("20 Hotel Rooms across 4 floors")}</li>
								<li>${__("10 Services (Breakfast, Spa, Laundry, etc.)")}</li>
								<li>${__("6 Packages (B&B, HB, AI, etc.)")}</li>
								<li>${__("15 Customers with diverse profiles")}</li>
								<li>${__("10 Reservations in various statuses")}</li>
								<li>${__("Active stays with folios and charges")}</li>
								<li>${__("Sample payments and housekeeping records")}</li>
							</ul>
						</div>

						<div id="status-area" style="display:none;" class="mb-3">
							<div class="alert alert-info" id="status-msg">
								<i class="fa fa-spinner fa-spin mr-2"></i>
								<span id="status-text">${__("Processing...")}</span>
							</div>
						</div>

						<div id="log-area" style="display:none;" class="mb-3">
							<div style="background:#f8f9fa; border:1px solid #dee2e6; border-radius:4px; padding:10px; max-height:300px; overflow-y:auto; font-family:monospace; font-size:12px;" id="log-output"></div>
						</div>

						<div class="d-flex gap-2" style="gap: 10px;">
							<button class="btn btn-primary" id="btn-add-test-data">
								<i class="fa fa-plus-circle mr-1"></i> ${__("Add Test Data")}
							</button>
							<button class="btn btn-danger" id="btn-delete-test-data">
								<i class="fa fa-trash mr-1"></i> ${__("Delete Test Data")}
							</button>
							<button class="btn btn-warning" id="btn-reset-test-data">
								<i class="fa fa-sync mr-1"></i> ${__("Reset Test Data")}
							</button>
						</div>
					</div>
				</div>

				<div class="card mt-3">
					<div class="card-body">
						<h6>${__("Direct Links")}</h6>
						<div class="d-flex flex-wrap" style="gap: 8px;">
							<a href="/app/hotel-room" class="btn btn-sm btn-outline-primary">${__("Rooms")}</a>
							<a href="/app/hotel-reservation" class="btn btn-sm btn-outline-primary">${__("Reservations")}</a>
							<a href="/app/hotel-customer" class="btn btn-sm btn-outline-primary">${__("Customers")}</a>
							<a href="/app/hotel-stay" class="btn btn-sm btn-outline-primary">${__("Stays")}</a>
							<a href="/app/hotel-folio" class="btn btn-sm btn-outline-primary">${__("Folios")}</a>
							<a href="/app/hotel-payment" class="btn btn-sm btn-outline-primary">${__("Payments")}</a>
						</div>
					</div>
				</div>
			</div>
		`);

		this.wrapper.find("#btn-add-test-data").on("click", () => this.add_test_data());
		this.wrapper.find("#btn-delete-test-data").on("click", () => this.confirm_delete());
		this.wrapper.find("#btn-reset-test-data").on("click", () => this.reset_test_data());
	}

	set_status(msg, type = "info") {
		const area = this.wrapper.find("#status-area");
		const alert = area.find(".alert");
		const text = area.find("#status-text");
		area.show();
		alert.removeClass("alert-info alert-success alert-danger").addClass(`alert-${type}`);
		text.text(msg);
	}

	log(msg) {
		const log = this.wrapper.find("#log-area");
		const output = this.wrapper.find("#log-output");
		log.show();
		output.append(`<div>${msg}</div>`);
		output.scrollTop(output[0].scrollHeight);
	}

	clear_log() {
		this.wrapper.find("#log-output").html("");
	}

	add_test_data() {
		this.clear_log();
		this.set_status(__("Creating test data... please wait."), "info");

		frappe.call({
			method: "hotel_pms.setup.seed_demo_data.seed",
			freeze: true,
			freeze_message: __("Creating test data..."),
			callback: (r) => {
				if (r.message) {
					this.set_status(__("Test data created successfully!"), "success");
					(r.message.log || []).forEach(l => this.log(l));
				} else {
					this.set_status(__("Test data creation completed."), "success");
				}
			},
			error: (err) => {
				this.set_status(__("Error creating test data. Check console for details."), "danger");
			}
		});
	}

	confirm_delete() {
		frappe.confirm(
			__("Are you sure you want to delete all test data? This cannot be undone."),
			() => this.delete_test_data()
		);
	}

	delete_test_data() {
		this.clear_log();
		this.set_status(__("Deleting test data..."), "info");

		frappe.call({
			method: "hotel_pms.setup.seed_demo_data.delete_test_data",
			freeze: true,
			freeze_message: __("Deleting test data..."),
			callback: (r) => {
				this.set_status(__("Test data deleted successfully."), "success");
				if (r.message) {
					(r.message.log || []).forEach(l => this.log(l));
				}
			},
			error: () => {
				this.set_status(__("Error deleting test data."), "danger");
			}
		});
	}

	reset_test_data() {
		frappe.confirm(
			__("This will delete and recreate all test data. Continue?"),
			() => {
				this.clear_log();
				this.set_status(__("Resetting test data..."), "info");

				frappe.call({
					method: "hotel_pms.setup.seed_demo_data.delete_test_data",
					freeze: true,
					freeze_message: __("Deleting old test data..."),
					callback: () => {
						frappe.call({
							method: "hotel_pms.setup.seed_demo_data.seed",
							freeze: true,
							freeze_message: __("Creating new test data..."),
							callback: (r) => {
								this.set_status(__("Test data reset complete!"), "success");
								if (r.message) {
									(r.message.log || []).forEach(l => this.log(l));
								}
							}
						});
					}
				});
			}
		);
	}
}
