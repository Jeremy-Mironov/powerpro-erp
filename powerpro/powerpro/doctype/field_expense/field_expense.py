import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt


class FieldExpense(Document):
    def before_insert(self):
        self.submitted_by = frappe.session.user

    def validate(self):
        if flt(self.amount) <= 0:
            frappe.throw(_("Amount must be positive"))
        if self.status == "Rejected" and not self.reject_reason:
            frappe.throw(_("Give a reason for rejecting"))
        if self.status == "Booked" and not self.purchase_invoice:
            frappe.throw(_("Booked expenses need a Purchase Invoice — use the Book button"))
        roles = set(frappe.get_roles())
        if not self.is_new() and self.has_value_changed("status") and self.status in ("Approved", "Booked", "Rejected"):
            if not roles & {"PP Owner", "PP Estimator", "PP Bookkeeper", "System Manager"}:
                frappe.throw(_("Only the office can approve, book or reject expenses"))


@frappe.whitelist()
def book(expense):
    # Turn an approved expense into a draft Purchase Invoice against the project (feeds ERPNext job costing)
    doc = frappe.get_doc("Field Expense", expense)
    doc.check_permission("write")
    if doc.purchase_invoice:
        return doc.purchase_invoice
    if not doc.supplier:
        frappe.throw(_("Pick the Supplier first"))
    item = frappe.db.get_value("Item", {"item_code": "Field expense"}, "name") or _ensure_expense_item()
    pi = frappe.get_doc({
        "doctype": "Purchase Invoice", "supplier": doc.supplier, "posting_date": doc.expense_date,
        "project": doc.project, "bill_no": doc.name, "remarks": f"{doc.category}: {doc.description or ''} ({doc.vendor_name})",
        "items": [{"item_code": item, "qty": 1, "rate": doc.amount, "project": doc.project,
                   "description": f"{doc.category} — {doc.vendor_name}: {doc.description or ''}"}],
    })
    pi.flags.ignore_permissions = True
    pi.insert()
    doc.db_set({"purchase_invoice": pi.name, "status": "Booked"})
    return pi.name


def _ensure_expense_item():
    if not frappe.db.exists("Item", "Field expense"):
        frappe.get_doc({"doctype": "Item", "item_code": "Field expense", "item_name": "Field expense",
                        "item_group": ("Services" if frappe.db.exists("Item Group", "Services")
                                       else frappe.db.get_value("Item Group", {"is_group": 0}, "name")),
                        "stock_uom": "Nos", "is_stock_item": 0, "is_purchase_item": 1, "is_sales_item": 0,
                        "description": "Receipt-based field expense booked against a project"}).insert(ignore_permissions=True)
    return "Field expense"
