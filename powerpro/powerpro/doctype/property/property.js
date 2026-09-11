frappe.ui.form.on("Property", {
    refresh(frm) {
        powerpro.notes.render(frm, {property: frm.doc.name, customer: frm.doc.customer});
        if (frm.is_new()) return;
        frm.add_custom_button(__("Project"), () => frappe.new_doc("Project", {customer: frm.doc.customer, pp_property: frm.doc.name}), __("Create"));
        frm.add_custom_button(__("Service Request"), () => frappe.new_doc("Service Request", {customer: frm.doc.customer, property: frm.doc.name}), __("Create"));
        frm.add_custom_button(__("Note"), () => powerpro.notes.add(frm, {property: frm.doc.name, customer: frm.doc.customer}), __("Create"));
        frm.add_custom_button(__("Open in Google Maps"), () => window.open(powerpro.geo.url("search", powerpro.geo.address_of(frm.doc))));
        frm.add_custom_button(__("Re-geocode"), () => {
            frappe.call({method: "powerpro.geo.regeocode", args: {property: frm.doc.name}}).then(() => frm.reload_doc());
        });
    }
});
