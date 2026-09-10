import frappe

ROLES = [
    ("PP Owner", 1),
    ("PP Dispatcher", 0),
    ("PP Estimator", 0),
    ("PP Field Tech", 0),
    ("PP Shop", 0),
    ("PP Bookkeeper", 1),
    ("PP Integration", 0),
]


def ensure_roles():
    for name, two_fa in ROLES:
        if not frappe.db.exists("Role", name):
            frappe.get_doc({
                "doctype": "Role", "role_name": name, "desk_access": 1,
                "is_custom": 1, "two_factor_auth": two_fa,
            }).insert(ignore_permissions=True)
    frappe.db.commit()


def before_install():
    ensure_roles()


def after_install():
    ensure_roles()
    # Touch the settings single so defaults are materialised
    s = frappe.get_single("PowerPro Settings")
    s.flags.ignore_permissions = True
    s.save()


def after_migrate():
    ensure_roles()
