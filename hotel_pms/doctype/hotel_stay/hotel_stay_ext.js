frappe.ui.form.on("Hotel Stay", {
    refresh(frm) {
        if (frm.doc.stay_status === "In House" || frm.doc.stay_status === "Extended") {

            frm.add_custom_button(__("Check Out"), () => {
                frappe.call({
                    method: "hotel_pms.api.checkout.get_checkout_summary",
                    args: { stay_name: frm.doc.name },
                    callback(r) {
                        const s = r.message;
                        const balance = s.balance_due || 0;
                        let msg = `<b>Total Charges:</b> ${format_currency(s.total_charges)}<br>
                                   <b>Total Paid:</b> ${format_currency(s.total_paid)}<br>
                                   <b>Balance Due:</b> ${format_currency(balance)}`;
                        if (balance > 0) {
                            msg += `<br><br><span class="text-danger">Outstanding balance must be settled.</span>`;
                        }
                        frappe.confirm(msg, () => {
                            frappe.call({
                                method: "hotel_pms.api.checkout.checkout_stay",
                                args: { stay_name: frm.doc.name, force: balance <= 0 ? 0 : 0 },
                                callback(r2) { frm.reload_doc(); }
                            });
                        });
                    }
                });
            }, __("Actions"));

            frm.add_custom_button(__("Post Charge"), () => {
                frappe.prompt([
                    { label: "Charge Type", fieldname: "charge_type", fieldtype: "Select",
                      options: ["Room","Food","Restaurant","Bar","Spa","Activity","Transport","Laundry","Extra Bed","Late Checkout","Other"].join("\n"), reqd: 1 },
                    { label: "Description", fieldname: "description", fieldtype: "Data", reqd: 1 },
                    { label: "Amount", fieldname: "amount", fieldtype: "Currency", reqd: 1 },
                ], (vals) => {
                    frappe.call({
                        method: "hotel_pms.api.folio.add_charge",
                        args: { folio_name: frm.doc.folio, charge_type: vals.charge_type, description: vals.description, amount: vals.amount },
                        callback(r) { frm.reload_doc(); frappe.msgprint("Charge posted."); }
                    });
                }, __("Post Folio Charge"));
            }, __("Actions"));

            frm.add_custom_button(__("Post Payment"), () => {
                frappe.prompt([
                    { label: "Amount", fieldname: "amount", fieldtype: "Currency", reqd: 1 },
                    { label: "Payment Type", fieldname: "payment_type", fieldtype: "Select",
                      options: ["Cash","Card","Bank Transfer","Online","Voucher","City Ledger","Deposit"].join("\n"), reqd: 1 },
                    { label: "Reference", fieldname: "reference", fieldtype: "Data" },
                ], (vals) => {
                    frappe.call({
                        method: "hotel_pms.api.payment.post_payment",
                        args: { folio_name: frm.doc.folio, amount: vals.amount, payment_type: vals.payment_type, reference: vals.reference },
                        callback(r) { frm.reload_doc(); frappe.msgprint(`Payment posted. Balance: ${format_currency(r.message.balance_due)}`); }
                    });
                }, __("Post Payment"));
            }, __("Actions"));
        }
    }
});

function format_currency(val) {
    return parseFloat(val || 0).toLocaleString("en-US", { style: "currency", currency: "USD" });
}
