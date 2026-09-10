frappe.ui.form.on("Service Request", {
    refresh(frm) {
        if (frm.is_new()) return;
        if (!frm.doc.project) {
            frm.add_custom_button(__("Job"), () => {
                frappe.new_doc("Project", {
                    customer: frm.doc.customer,
                    pp_property: frm.doc.property,
                    pp_service_request: frm.doc.name,
                    project_name: frm.doc.description ? frm.doc.description.slice(0, 80) : ""
                });
            }, __("Create"));
        }
        if (!frm.doc.quotation && frm.doc.customer) {
            frm.add_custom_button(__("Quotation"), () => {
                frappe.new_doc("Quotation", {
                    quotation_to: "Customer",
                    party_name: frm.doc.customer,
                    pp_service_request: frm.doc.name,
                    pp_property: frm.doc.property
                });
            }, __("Create"));
        }
    }
});
