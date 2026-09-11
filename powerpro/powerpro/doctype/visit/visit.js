function ppGetPosition(cb) {
    // Browser geolocation (phone GPS); falls back to no coordinates
    if (!navigator.geolocation) return cb(null);
    navigator.geolocation.getCurrentPosition(
        (pos) => cb({lat: pos.coords.latitude, lng: pos.coords.longitude}),
        () => cb(null), {enableHighAccuracy: true, timeout: 8000, maximumAge: 60000}
    );
}

frappe.ui.form.on("Visit", {
    refresh(frm) {
        powerpro.notes.render(frm, {visit: frm.doc.name, project: frm.doc.project, property: frm.doc.property, customer: frm.doc.customer});
        if (frm.is_new()) return;
        if (!frm.doc.check_in) {
            frm.add_custom_button(__("Check in"), () => ppGetPosition((p) => {
                frm.set_value("check_in", frappe.datetime.now_datetime());
                frm.set_value("status", "On site");
                if (p) { frm.set_value("checkin_lat", p.lat); frm.set_value("checkin_lng", p.lng); }
                frm.save();
            })).addClass("btn-primary");
        } else if (!frm.doc.check_out) {
            frm.add_custom_button(__("Check out"), () => ppGetPosition((p) => {
                frm.set_value("check_out", frappe.datetime.now_datetime());
                frm.set_value("status", "Done");
                if (p) { frm.set_value("checkout_lat", p.lat); frm.set_value("checkout_lng", p.lng); }
                frm.save();
            })).addClass("btn-primary");
        }
        frm.add_custom_button(__("Photo"), () => frappe.new_doc("Job Photo", {project: frm.doc.project, visit: frm.doc.name}), __("Create"));
        frm.add_custom_button(__("Note"), () => powerpro.notes.add(frm, {visit: frm.doc.name, project: frm.doc.project, property: frm.doc.property, customer: frm.doc.customer}), __("Create"));
        frm.add_custom_button(__("Expense"), () => frappe.new_doc("Field Expense", {project: frm.doc.project, visit: frm.doc.name}), __("Create"));
        if (frm.doc.warehouse) {
            frm.add_custom_button(__("Issue materials"), () => frappe.new_doc("Stock Entry", {stock_entry_type: "Material Issue", from_warehouse: frm.doc.warehouse, project: frm.doc.project}), __("Create"));
            frm.add_custom_button(__("Transfer to van"), () => {
                frappe.db.get_single_value("PowerPro Settings", "shop_warehouse").then(shop =>
                    frappe.new_doc("Stock Entry", {stock_entry_type: "Material Transfer", from_warehouse: shop, to_warehouse: frm.doc.warehouse, project: frm.doc.project}));
            }, __("Create"));
        }
        frm.add_custom_button(__("Timesheet"), () => frappe.new_doc("Timesheet", {parent_project: frm.doc.project}), __("Create"));
        if (frm.doc.latitude && frm.doc.longitude) {
            frm.add_custom_button(__("Navigate"), () => window.open(`https://www.google.com/maps/dir/?api=1&destination=${frm.doc.latitude},${frm.doc.longitude}`));
        }
    },
    checklist_template(frm) {
        if (!frm.doc.checklist_template || (frm.doc.checklist || []).length) return;
        frappe.db.get_doc("Visit Checklist Template", frm.doc.checklist_template).then(tpl => {
            (tpl.items || []).forEach(r => { const row = frm.add_child("checklist"); row.task = r.task; row.is_required = r.is_required; });
            frm.refresh_field("checklist");
        });
    },
    van(frm) {
        if (frm.doc.van) frappe.db.get_value("Van", frm.doc.van, "warehouse").then(r => frm.set_value("warehouse", r.message.warehouse));
    }
});
