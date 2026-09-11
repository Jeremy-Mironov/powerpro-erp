"""Field notes inherited down the chain customer -> property -> project -> visit."""
import frappe
from frappe.utils import cstr

from powerpro.powerpro.doctype.field_note.field_note import visible_levels


@frappe.whitelist()
def get_notes(customer=None, property=None, project=None, visit=None, limit=50):
    """Notes relevant to a form, most specific first, pinned first, visibility-filtered."""
    levels = visible_levels(frappe.session.user)
    conds, vals = [], {}
    for key, val in (("visit", visit), ("project", project), ("property", property), ("customer", customer)):
        if val:
            conds.append(f"`{key}` = %({key})s")
            vals[key] = val
    if not conds:
        return []
    vals["levels"] = tuple(levels)
    rows = frappe.db.sql(f"""
        select name, note_type, visibility, pinned, title, content, image, author_name, author_role,
               customer, property, project, visit, creation
        from `tabField Note`
        where visibility in %(levels)s and ({' or '.join(conds)})
        order by pinned desc, creation desc
        limit {int(limit)}""", vals, as_dict=True)
    for r in rows:
        # which level of the chain the note belongs to (most specific link that is set)
        r["scope"] = "Visit" if r.visit else "Project" if r.project else "Property" if r.property else "Customer"
        r["scope_name"] = r.visit or r.project or r.property or r.customer
        r["excerpt"] = cstr(r.content)
    return rows
