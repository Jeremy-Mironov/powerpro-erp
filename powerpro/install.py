"""Install / migrate hooks. Everything here is idempotent: it can run on every
`bench migrate` and only adds what is missing."""
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

PROJECT_TYPES = [
    "Service call", "Emergency", "Safety check", "Panel upgrade", "EV charger",
    "Remodel", "New construction", "Generator", "Commercial project", "Warranty", "Other",
]

# Our DocTypes appear inside ERPNext's own sidebars instead of a separate "PowerPro" section.
# sidebar title -> [(anchor link_to, [(link_to, link_type, label), ...]), ...]
SIDEBAR_ITEMS = {
    "Projects": [
        ("Project", [("Visit", "DocType", "Visits"), ("Change Order", "DocType", "Change Orders"),
                     ("Permit", "DocType", "Permits"), ("Job Photo", "DocType", "Photos")]),
        ("Projects Settings", [("PowerPro Settings", "DocType", "Power Professor Settings")]),
    ],
    "CRM": [
        ("Customer", [("Service Request", "DocType", "Service Requests"), ("Property", "DocType", "Properties"),
                      ("Call", "DocType", "Calls")]),
    ],
    "Stock": [
        ("Warehouse", [("Van", "DocType", "Vans")]),
    ],
}


def ensure_roles():
    for name, two_fa in ROLES:
        if not frappe.db.exists("Role", name):
            frappe.get_doc({
                "doctype": "Role", "role_name": name, "desk_access": 1,
                "is_custom": 1, "two_factor_auth": two_fa,
            }).insert(ignore_permissions=True)


def ensure_project_types():
    if not frappe.db.exists("DocType", "Project Type"):
        return
    for name in PROJECT_TYPES:
        if not frappe.db.exists("Project Type", name):
            frappe.get_doc({"doctype": "Project Type", "project_type": name}).insert(ignore_permissions=True)


def ensure_sidebar_items():
    """Add our links to ERPNext's Projects / CRM / Stock sidebars (Frappe 16)."""
    if not frappe.db.exists("DocType", "Workspace Sidebar"):
        return
    for title, groups in SIDEBAR_ITEMS.items():
        if not frappe.db.exists("Workspace Sidebar", title):
            continue
        sb = frappe.get_doc("Workspace Sidebar", title)
        present = {(i.link_type, i.link_to) for i in sb.items}
        changed = False
        for anchor, entries in groups:
            pos = next((i for i, it in enumerate(sb.items) if it.type == "Link" and it.link_to == anchor), None)
            child = sb.items[pos].child if pos is not None else 0
            insert_at = pos + 1 if pos is not None else len(sb.items)
            for link_to, link_type, label in entries:
                if (link_type, link_to) in present:
                    continue
                if link_type == "DocType" and not frappe.db.exists("DocType", link_to):
                    continue
                row = sb.append("items", {"type": "Link", "label": label, "link_type": link_type,
                                          "link_to": link_to, "child": child})
                sb.items.remove(row)
                sb.items.insert(insert_at, row)
                insert_at += 1
                present.add((link_type, link_to))
                changed = True
        if not changed:
            continue
        for i, it in enumerate(sb.items, 1):
            it.idx = i
        sb.flags.ignore_permissions = True
        # in_import stops developer_mode from exporting the (ERPNext-owned) sidebar to erpnext's folder
        frappe.flags.in_import = True
        try:
            sb.save()
        finally:
            frappe.flags.in_import = False


def remove_old_artifacts():
    """v1-v3 shipped a separate 'PowerPro' workspace and a Job DocType. Clean them up if present."""
    frappe.flags.in_patch = True  # lets standard Report / DocType records be deleted outside developer mode
    try:
        _remove_old_artifacts()
    finally:
        frappe.flags.in_patch = False


def _remove_old_artifacts():
    for dt, name in (("Desktop Icon", "PowerPro"), ("Workspace Sidebar", "PowerPro"), ("Workspace", "PowerPro"),
                     ("Report", "Job Costing")):
        if frappe.db.exists(dt, name):
            try:
                frappe.delete_doc(dt, name, force=True, ignore_permissions=True, ignore_missing=True)
            except Exception:
                frappe.log_error(title=f"PowerPro cleanup: could not delete {dt} {name}")
    for cf in frappe.get_all("Custom Field", filters={"fieldname": "pp_job"}, pluck="name"):
        frappe.delete_doc("Custom Field", cf, force=True, ignore_permissions=True)
    if frappe.db.exists("DocType", "Job") and frappe.db.get_value("DocType", "Job", "module") == "PowerPro":
        frappe.delete_doc("DocType", "Job", force=True, ignore_permissions=True)


def before_install():
    ensure_roles()
    frappe.db.commit()


def after_install():
    _all()


def after_migrate():
    _all()


def _all():
    ensure_roles()
    ensure_project_types()
    remove_old_artifacts()
    ensure_sidebar_items()
    s = frappe.get_single("PowerPro Settings")
    s.flags.ignore_permissions = True
    s.save()
    frappe.db.commit()
