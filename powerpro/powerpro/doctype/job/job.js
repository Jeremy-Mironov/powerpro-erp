frappe.ui.form.on("Job", {
    refresh(frm) {
        const colors = {"Scheduled":"blue","In progress":"orange","On hold":"grey","Complete":"green","Invoiced":"green",
                        "Paid":"green","Closed":"darkgrey","Under warranty":"purple","Disputed":"red","Cancelled":"red"};
        frm.page.set_indicator(frm.doc.status, colors[frm.doc.status] || "blue");
        if (frm.is_new()) return;
        frm.add_custom_button(__("Visit"), () => frappe.new_doc("Visit", {job: frm.doc.name}), __("Create"));
        frm.add_custom_button(__("Change Order"), () => frappe.new_doc("Change Order", {job: frm.doc.name}), __("Create"));
        frm.add_custom_button(__("Photo"), () => frappe.new_doc("Job Photo", {job: frm.doc.name}), __("Create"));
        if (!frm.doc.permit) frm.add_custom_button(__("Permit"), () => frappe.new_doc("Permit", {job: frm.doc.name}), __("Create"));
        frm.add_custom_button(__("Material Request"), () => frappe.new_doc("Material Request", {pp_job: frm.doc.name, material_request_type: "Material Issue"}), __("Create"));
        frm.add_custom_button(__("Sales Invoice"), () => frappe.new_doc("Sales Invoice", {customer: frm.doc.customer, pp_job: frm.doc.name}), __("Create"));
        frm.add_custom_button(__("Refresh costs"), () => {
            frappe.call({method: "powerpro.costing.refresh_job_costs", args: {job: frm.doc.name}}).then(() => frm.reload_doc());
        });
        if (frm.doc.needs_owner_approval && !frm.doc.owner_approved_on && frappe.user.has_role("PP Owner")) {
            frm.add_custom_button(__("Approve as owner"), () => {
                frm.set_value("owner_approved_by", frappe.session.user);
                frm.set_value("owner_approved_on", frappe.datetime.now_datetime());
                frm.save();
            }).addClass("btn-primary");
        }
    },
    property(frm) {
        if (frm.doc.property && !frm.doc.customer) {
            frappe.db.get_value("Property", frm.doc.property, "customer").then(r => frm.set_value("customer", r.message.customer));
        }
    }
});
