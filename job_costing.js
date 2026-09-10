frappe.query_reports["Job Costing"] = {
    filters: [
        {fieldname: "from_date", label: __("Scheduled from"), fieldtype: "Date"},
        {fieldname: "status", label: __("Status"), fieldtype: "Select",
         options: "\nScheduled\nIn progress\nOn hold\nComplete\nInvoiced\nPaid\nClosed\nUnder warranty\nDisputed\nCancelled"},
        {fieldname: "customer", label: __("Customer"), fieldtype: "Link", options: "Customer"},
        {fieldname: "lead_tech", label: __("Lead tech"), fieldtype: "Link", options: "Employee"},
    ]
};
