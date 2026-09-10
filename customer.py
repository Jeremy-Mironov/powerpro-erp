from powerpro.utils import guard_mirror, normalize_e164


def validate(doc, method=None):
    guard_mirror(doc, flag="pp_is_mirror")
    doc.pp_phone_e164 = normalize_e164(doc.get("mobile_no"))
