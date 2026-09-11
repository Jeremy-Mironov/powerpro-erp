frappe.ui.form.on("Field Expense", {
    refresh(frm) {
        if (frm.is_new() || frm.doc.status === "Booked") return;
        if (frappe.user.has_role(["PP Owner", "PP Estimator", "PP Bookkeeper", "System Manager"])) {
            if (frm.doc.status === "Submitted") frm.add_custom_button(__("Approve"), () => { frm.set_value("status", "Approved"); frm.save(); }).addClass("btn-primary");
            if (frm.doc.status === "Approved") frm.add_custom_button(__("Book as Purchase Invoice"), () => {
                frappe.call({method: "powerpro.powerpro.doctype.field_expense.field_expense.book", args: {expense: frm.doc.name}})
                    .then(r => { if (r.message) frappe.set_route("Form", "Purchase Invoice", r.message); });
            }).addClass("btn-primary");
            if (frm.doc.status !== "Rejected") frm.add_custom_button(__("Reject"), () => {
                frappe.prompt(__("Reason"), (v) => { frm.set_value("reject_reason", v.value); frm.set_value("status", "Rejected"); frm.save(); }, __("Reject expense"));
            });
        }
    }
});
