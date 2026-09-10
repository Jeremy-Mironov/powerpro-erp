app_name = "powerpro"
app_title = "PowerPro"
app_publisher = "Power Professor LLC"
app_description = "Field service layer for Power Professor on ERPNext: requests, jobs, visits, permits, change orders, calls"
app_email = "jeremy@powerpro.info"
app_license = "MIT"
required_apps = ["erpnext"]

# Runs before DocTypes are synced, so permissions can reference our roles
before_install = "powerpro.install.before_install"
after_install = "powerpro.install.after_install"
after_migrate = "powerpro.install.after_migrate"

# Roles and custom fields ship with the app
fixtures = [
    {"dt": "Role", "filters": [["name", "like", "PP %"]]},
    {"dt": "Custom Field", "filters": [["module", "=", "PowerPro"]]},
]

doc_events = {
    "Contact": {"validate": "powerpro.overrides.contact.set_e164"},
    "Customer": {"validate": "powerpro.overrides.customer.validate"},
    "Quotation": {
        "validate": "powerpro.overrides.quotation.validate",
        "before_submit": "powerpro.overrides.quotation.before_submit",
    },
    "Sales Invoice": {
        "validate": "powerpro.overrides.mirror.guard",
        "on_submit": "powerpro.overrides.costing.on_change",
        "on_cancel": "powerpro.overrides.costing.on_change",
        "on_update_after_submit": "powerpro.overrides.costing.on_change",
    },
    "Stock Entry": {
        "on_submit": "powerpro.overrides.costing.on_change",
        "on_cancel": "powerpro.overrides.costing.on_change",
    },
    "Purchase Invoice": {
        "on_submit": "powerpro.overrides.costing.on_change",
        "on_cancel": "powerpro.overrides.costing.on_change",
    },
    "Timesheet": {
        "on_submit": "powerpro.overrides.costing.on_change",
        "on_cancel": "powerpro.overrides.costing.on_change",
    },
    "Payment Entry": {
        "on_submit": "powerpro.overrides.costing.on_payment",
        "on_cancel": "powerpro.overrides.costing.on_payment",
    },
}

scheduler_events = {
    "daily": ["powerpro.tasks.daily"],
}
