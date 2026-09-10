frappe.ui.form.on("Visit", {
    refresh(frm) {
        if (frm.is_new()) return;
        if (!frm.doc.check_in) frm.add_custom_button(__("Check in"), () => { frm.set_value("check_in", frappe.datetime.now_datetime()); frm.set_value("status", "On site"); frm.save(); });
        else if (!frm.doc.check_out) frm.add_custom_button(__("Check out"), () => { frm.set_value("check_out", frappe.datetime.now_datetime()); frm.set_value("status", "Done"); frm.save(); });
        frm.add_custom_button(__("Photo"), () => frappe.new_doc("Job Photo", {project: frm.doc.project, visit: frm.doc.name}), __("Create"));
        if (frm.doc.warehouse) frm.add_custom_button(__("Issue materials"), () => frappe.new_doc("Stock Entry", {stock_entry_type: "Material Issue", from_warehouse: frm.doc.warehouse, project: frm.doc.project}), __("Create"));
        frm.add_custom_button(__("Timesheet"), () => frappe.new_doc("Timesheet", {parent_project: frm.doc.project}), __("Create"));
    },
    van(frm) {
        if (frm.doc.van) frappe.db.get_value("Van", frm.doc.van, "warehouse").then(r => frm.set_value("warehouse", r.message.warehouse));
    }
});
