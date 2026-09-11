app_name = "powerpro"
app_title = "PowerPro"
app_publisher = "Power Professor LLC"
app_description = "Field service layer for Power Professor on ERPNext: requests, jobs (Project), visits, permits, change orders, notes, calls"
app_email = "jeremy@powerpro.info"
app_license = "MIT"
required_apps = ["erpnext"]

# Runs before DocTypes are synced, so permissions can reference our roles
before_install = "powerpro.install.before_install"
after_install = "powerpro.install.after_install"
after_migrate = "powerpro.install.after_migrate"

# Roles ship as fixtures. Custom fields, property setters and permissions on
# standard DocTypes live in powerpro/powerpro/custom/*.json (synced on migrate).
fixtures = [
    {"dt": "Role", "filters": [["name", "like", "PP %"]]},
]

# Shared desk JS (field-notes panel) and per-DocType client scripts on ERPNext forms
app_include_js = ["/assets/powerpro/js/notes.js"]
doctype_js = {
    "Project": "public/js/project.js",
    "Customer": "public/js/customer.js",
}
doctype_list_js = {"Project": "public/js/project_list.js"}

doc_events = {
    "Project": {"validate": "powerpro.overrides.project.validate"},
    "Contact": {"validate": "powerpro.overrides.contact.set_e164"},
    "Customer": {"validate": "powerpro.overrides.customer.validate"},
    "Quotation": {
        "validate": "powerpro.overrides.quotation.validate",
        "before_submit": "powerpro.overrides.quotation.before_submit",
    },
    "Sales Order": {"after_insert": "powerpro.overrides.project.on_sales_order"},
    "Sales Invoice": {
        "validate": "powerpro.overrides.mirror.guard",
        "on_submit": "powerpro.overrides.project.on_invoice_change",
        "on_cancel": "powerpro.overrides.project.on_invoice_change",
    },
    "Payment Entry": {
        "on_submit": "powerpro.overrides.project.on_payment",
        "on_cancel": "powerpro.overrides.project.on_payment",
    },
}

# Field notes are filtered by visibility level (Everyone / Office / Owner)
permission_query_conditions = {
    "Field Note": "powerpro.powerpro.doctype.field_note.field_note.get_permission_query_conditions",
}
has_permission = {
    "Field Note": "powerpro.powerpro.doctype.field_note.field_note.has_permission",
}

scheduler_events = {
    "daily": ["powerpro.tasks.daily"],
}
