frappe.ui.form.on("Field Note", {
    refresh(frm) {
        const rows = [["customer", "Customer"], ["property", "Property"], ["project", "Project"], ["visit", "Visit"]];
        rows.forEach(([f, dt]) => { if (frm.doc[f]) frm.add_custom_button(__(dt), () => frappe.set_route("Form", dt, frm.doc[f]), __("Open")); });
    },
    visit(frm) { if (frm.doc.visit) frappe.db.get_value("Visit", frm.doc.visit, ["project", "property", "customer"]).then(r => { if (r.message) { ["project","property","customer"].forEach(k => { if (!frm.doc[k]) frm.set_value(k, r.message[k]); }); } }); },
    project(frm) { if (frm.doc.project) frappe.db.get_value("Project", frm.doc.project, ["customer", "pp_property"]).then(r => { if (r.message) { if (!frm.doc.customer) frm.set_value("customer", r.message.customer); if (!frm.doc.property) frm.set_value("property", r.message.pp_property); } }); },
    property(frm) { if (frm.doc.property && !frm.doc.customer) frappe.db.get_value("Property", frm.doc.property, "customer").then(r => { if (r.message) frm.set_value("customer", r.message.customer); }); }
});
