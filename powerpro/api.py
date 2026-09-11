"""Endpoints for n8n. Call as the integration user with an API key:
POST /api/method/powerpro.api.log_call  etc.  Payload as JSON body."""
import json

import frappe
from frappe.utils import now_datetime

from powerpro.utils import find_customer_by_phone, normalize_e164

ALLOWED = ("PP Integration", "System Manager")


def _json(v):
    if isinstance(v, str):
        try:
            return json.loads(v)
        except ValueError:
            return v
    return v


@frappe.whitelist()
def upsert(doctype, key_field, key_value, values):
    """Idempotent create-or-update by an external id (jobber_id, call_sid...)."""
    frappe.only_for(ALLOWED)
    values = _json(values) or {}
    name = frappe.db.get_value(doctype, {key_field: key_value}, "name")
    if name:
        doc = frappe.get_doc(doctype, name)
        doc.update(values)
        doc.flags.ignore_mirror = True
        doc.save()
        return {"name": doc.name, "created": False}
    doc = frappe.get_doc({"doctype": doctype, key_field: key_value, **values})
    doc.flags.ignore_mirror = True
    doc.insert()
    return {"name": doc.name, "created": True}


@frappe.whitelist()
def log_call(call_sid, direction="Inbound", status="In progress", received_at=None, from_number=None,
             to_number=None, tracking_number=None, source_label=None, duration_sec=0,
             recording_url=None, transcript=None, raw=None):
    frappe.only_for(ALLOWED)
    values = {
        "direction": direction, "status": status, "received_at": received_at or now_datetime(),
        "from_e164": normalize_e164(from_number), "to_e164": normalize_e164(to_number),
        "tracking_number": normalize_e164(tracking_number), "source_label": source_label,
        "duration_sec": int(duration_sec or 0),
    }
    if recording_url:
        values["recording_url"] = recording_url
    if transcript:
        values["transcript"] = transcript
    if raw is not None:
        values["raw"] = raw if isinstance(raw, str) else json.dumps(raw)
    return upsert("Call", "call_sid", call_sid, values)


@frappe.whitelist()
def log_sms(sid, direction, from_number, to_number, body, received_at=None):
    """Store an SMS as a Communication on the customer's timeline (or on the open Service Request)."""
    frappe.only_for(ALLOWED)
    if frappe.db.exists("Communication", {"message_id": sid}):
        return {"name": frappe.db.get_value("Communication", {"message_id": sid}, "name"), "created": False}
    frm, to = normalize_e164(from_number), normalize_e164(to_number)
    other = frm if direction == "Inbound" else to
    customer, contact = find_customer_by_phone(other)
    ref_dt, ref_name = None, None
    sr = frappe.db.get_value("Service Request", {"phone_e164": other, "status": ("in", ["New", "Contacted", "Visit scheduled", "Quoted"])}, "name")
    if sr:
        ref_dt, ref_name = "Service Request", sr
    elif customer:
        ref_dt, ref_name = "Customer", customer
    doc = frappe.get_doc({
        "doctype": "Communication", "communication_type": "Communication", "communication_medium": "SMS",
        "sent_or_received": "Received" if direction == "Inbound" else "Sent",
        "subject": (body or "")[:100] or "SMS", "content": body or "", "phone_no": other,
        "message_id": sid, "communication_date": received_at or now_datetime(),
        "reference_doctype": ref_dt, "reference_name": ref_name, "status": "Open",
    })
    doc.insert(ignore_permissions=True)
    return {"name": doc.name, "created": True, "customer": customer, "service_request": sr}


@frappe.whitelist()
def make_sales_order_from_project(project):
    """Line items of a job: a draft Sales Order built from the project's quotation, linked to the project."""
    from erpnext.selling.doctype.quotation.quotation import make_sales_order

    doc = frappe.get_doc("Project", project)
    doc.check_permission("write")
    if doc.sales_order:
        return doc.sales_order
    if not doc.pp_quotation:
        frappe.throw("This project has no quotation; create the Sales Order by hand")
    so = make_sales_order(doc.pp_quotation)
    so.project = doc.name
    for row in so.items:
        row.project = doc.name
    so.insert()
    doc.db_set("sales_order", so.name, update_modified=False)
    return so.name
