frappe.ui.form.on("Service Request", {
    refresh(frm) {
        if (!frm.is_new() && !frm.doc.job) {
            frm.add_custom_button(__("Job"), () => {
                frappe.new_doc("Job", {
                    customer: frm.doc.customer,
                    property: frm.doc.property,
                    service_request: frm.doc.name,
                    title: frm.doc.description ? frm.doc.description.slice(0, 80) : ""
                });
            }, __("Create"));
        }
        if (!frm.is_new() && !frm.doc.quotation && frm.doc.customer) {
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
