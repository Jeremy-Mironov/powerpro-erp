// PowerPro: Project list shows the job status. Extends ERPNext's own listview settings.
(function () {
    const base = frappe.listview_settings["Project"] || {};
    const colors = {
        "Scheduled": "blue", "In progress": "orange", "On hold": "grey", "Complete": "green",
        "Invoiced": "green", "Paid": "green", "Closed": "darkgrey", "Under warranty": "purple",
        "Disputed": "red", "Cancelled": "red"
    };
    frappe.listview_settings["Project"] = Object.assign({}, base, {
        add_fields: [...(base.add_fields || []), "pp_status", "pp_property", "customer", "pp_lead_tech"],
        filters: [["pp_status", "not in", ["Closed", "Cancelled"]]],
        get_indicator(doc) {
            const s = doc.pp_status || doc.status;
            return [__(s), colors[s] || "blue", "pp_status,=," + s];
        }
    });
})();
