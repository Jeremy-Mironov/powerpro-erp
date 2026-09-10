from powerpro.utils import normalize_e164


def set_e164(doc, method=None):
    doc.pp_phone_e164 = normalize_e164(doc.get("mobile_no") or doc.get("phone"))
