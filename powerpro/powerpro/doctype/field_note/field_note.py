import re

import frappe
from frappe import _
from frappe.model.document import Document

OFFICE_ROLES = {"PP Owner", "PP Dispatcher", "PP Estimator", "PP Shop", "PP Bookkeeper", "PP Integration", "System Manager"}
OWNER_ROLES = {"PP Owner", "System Manager"}
ROLE_LABELS = [("System Manager", "Admin"), ("PP Owner", "Owner"), ("PP Estimator", "Estimator"),
               ("PP Dispatcher", "Dispatcher"), ("PP Shop", "Shop"), ("PP Bookkeeper", "Bookkeeper"),
               ("PP Field Tech", "Field tech"), ("PP Integration", "Integration")]


def visible_levels(user=None):
    roles = set(frappe.get_roles(user))
    if user == "Administrator" or roles & OWNER_ROLES:
        return ["Everyone", "Office", "Owner"]
    if roles & OFFICE_ROLES:
        return ["Everyone", "Office"]
    return ["Everyone"]


def role_label(user):
    roles = set(frappe.get_roles(user))
    for role, label in ROLE_LABELS:
        if role in roles:
            return label
    return "User"


class FieldNote(Document):
    def validate(self):
        self.fill_links()
        if self.visibility not in visible_levels(frappe.session.user):
            frappe.throw(_("You cannot create notes visible to {0}").format(self.visibility))
        if not self.title:
            text = re.sub(r"<[^>]+>", " ", self.content or "")
            self.title = " ".join(text.split())[:80]
        if not self.author_role:
            self.author_role = role_label(self.owner or frappe.session.user)
        if not self.author_name:
            self.author_name = frappe.utils.get_fullname(self.owner or frappe.session.user)

    def fill_links(self):
        if self.visit and not self.project:
            self.project = frappe.db.get_value("Visit", self.visit, "project")
        if self.project and not (self.customer and self.property):
            p = frappe.db.get_value("Project", self.project, ["customer", "pp_property"], as_dict=True) or {}
            self.customer = self.customer or p.get("customer")
            self.property = self.property or p.get("pp_property")
        if self.property and not self.customer:
            self.customer = frappe.db.get_value("Property", self.property, "customer")
        if not (self.customer or self.property or self.project or self.visit):
            frappe.throw(_("A note needs a customer, property, project or visit"))


def get_permission_query_conditions(user=None):
    user = user or frappe.session.user
    levels = ", ".join(frappe.db.escape(v) for v in visible_levels(user))
    return f"`tabField Note`.visibility in ({levels})"


def has_permission(doc, ptype="read", user=None):
    user = user or frappe.session.user
    return doc.visibility in visible_levels(user)
