// PowerPro: ERPNext Project is the Job. Loaded on the Project form via hooks.doctype_js.
frappe.ui.form.on("Project", {
    refresh(frm) {
        const colors = {
            "Scheduled": "blue", "In progress": "orange", "On hold": "grey", "Complete": "green",
            "Invoiced": "green", "Paid": "green", "Closed": "darkgrey", "Under warranty": "purple",
            "Disputed": "red", "Cancelled": "red"
        };
        if (frm.doc.pp_status) frm.page.set_indicator(__(frm.doc.pp_status), colors[frm.doc.pp_status] || "blue");
        powerpro.notes.render(frm, { project: frm.doc.name, property: frm.doc.pp_property, customer: frm.doc.customer });
        if (frm.is_new()) return;

        frm.add_custom_button(__("Visit"), () => frappe.new_doc("Visit", { project: frm.doc.name }), __("Create"));
        frm.add_custom_button(__("Note"), () => powerpro.notes.add(frm, { project: frm.doc.name, property: frm.doc.pp_property, customer: frm.doc.customer }), __("Create"));
        frm.add_custom_button(__("Change Order"), () => frappe.new_doc("Change Order", { project: frm.doc.name }), __("Create"));
        frm.add_custom_button(__("Photo"), () => frappe.new_doc("Job Photo", { project: frm.doc.name }), __("Create"));
        frm.add_custom_button(__("Expense"), () => frappe.new_doc("Field Expense", { project: frm.doc.name }), __("Create"));
        if (!frm.doc.pp_permit) frm.add_custom_button(__("Permit"), () => frappe.new_doc("Permit", { project: frm.doc.name }), __("Create"));
        frm.add_custom_button(__("Sales Invoice"), () => frappe.new_doc("Sales Invoice", {
            customer: frm.doc.customer, project: frm.doc.name
        }), __("Create"));

        // Line items = the Sales Order of this job (from the quotation when there is one)
        if (frm.doc.sales_order) {
            frm.add_custom_button(__("Line items"), () => frappe.set_route("Form", "Sales Order", frm.doc.sales_order));
        } else if (frm.doc.pp_quotation) {
            frm.add_custom_button(__("Line items"), () => {
                frappe.call({ method: "powerpro.api.make_sales_order_from_project", args: { project: frm.doc.name } })
                    .then((r) => { if (r.message) frappe.set_route("Form", "Sales Order", r.message); });
            });
        } else if (frm.doc.customer) {
            frm.add_custom_button(__("Line items"), () => frappe.new_doc("Sales Order", {
                customer: frm.doc.customer, project: frm.doc.name, delivery_date: frappe.datetime.add_days(frappe.datetime.get_today(), 7)
            }));
        }

        if (frm.doc.pp_needs_owner_approval && !frm.doc.pp_owner_approved_on && frappe.user.has_role("PP Owner")) {
            frm.add_custom_button(__("Approve as owner"), () => {
                frm.set_value("pp_owner_approved_by", frappe.session.user);
                frm.set_value("pp_owner_approved_on", frappe.datetime.now_datetime());
                frm.save();
            }).addClass("btn-primary");
        }
        if (frm.doc.pp_property || (frm.doc.latitude && frm.doc.longitude)) {
            frm.add_custom_button(__("Navigate"), () => powerpro.geo.navigate(frm.doc.pp_property, frm.doc.latitude, frm.doc.longitude));
        }
    },
    pp_property(frm) {
        if (!frm.doc.pp_property) return;
        frappe.db.get_value("Property", frm.doc.pp_property, ["customer", "latitude", "longitude"]).then((r) => {
            if (!r.message) return;
            if (!frm.doc.customer) frm.set_value("customer", r.message.customer);
            frm.set_value("latitude", r.message.latitude);
            frm.set_value("longitude", r.message.longitude);
        });
    },
    setup(frm) {
        // Property picker shows only this customer's properties
        frm.set_query("pp_property", () => frm.doc.customer ? { filters: { customer: frm.doc.customer, is_active: 1 } } : {});
    }
});
