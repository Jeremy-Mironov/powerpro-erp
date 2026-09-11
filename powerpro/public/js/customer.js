// PowerPro: Customer form — field notes panel and quick-create buttons (Jobber-like client card)
frappe.ui.form.on("Customer", {
    refresh(frm) {
        powerpro.notes.render(frm, { customer: frm.doc.name });
        if (frm.is_new()) return;
        frm.add_custom_button(__("Property"), () => frappe.new_doc("Property", { customer: frm.doc.name }), __("Create"));
        frm.add_custom_button(__("Service Request"), () => frappe.new_doc("Service Request", { customer: frm.doc.name }), __("Create"));
        frm.add_custom_button(__("Project"), () => frappe.new_doc("Project", { customer: frm.doc.name }), __("Create"));
        frm.add_custom_button(__("Note"), () => powerpro.notes.add(frm, { customer: frm.doc.name }), __("Create"));
    }
});
