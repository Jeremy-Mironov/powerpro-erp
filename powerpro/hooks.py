app_name = "powerpro"
app_title = "PowerPro"
app_publisher = "Power Professor LLC"
app_description = "Field service layer for Power Professor on ERPNext: requests, jobs (Project), visits, permits, change orders, calls"
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

# Client scripts for ERPNext's Project form and list (the Job)
doctype_js = {"Project": "public/js/project.js"}
doctype_list_js = {"Project": "public/js/project_list.js"}

doc_events = {
    "Project": {"validate": "powerpro.overrides.project.validate"},
    "Contact": {"validate": "powerpro.overrides.contact.set_e164"},
    "Customer": {"validate": "powerpro.overrides.customer.validate"},
    "Quotation": {
        "validate": "powerpro.overrides.quotation.validate",
        "before_submit": "powerpro.overrides.quotation.before_submit",
    },
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

scheduler_events = {
    "daily": ["powerpro.tasks.daily"],
}
