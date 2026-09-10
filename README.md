# PowerPro — field service layer for ERPNext

Custom Frappe app for Power Professor LLC (Portland OR / Vancouver WA electricians).
It adds the field-service objects ERPNext lacks and wires them to ERPNext's own
Stock, Buying, Selling, Projects and HR modules. Everything that ERPNext already
has (Customer, Item, Warehouse, Quotation, Sales Invoice, Purchase Order,
Timesheet, Project, Employee, Vehicle) is used as-is.

Requires: Frappe 15/16 + ERPNext 15/16.

## What is in the box

| DocType | Purpose |
|---|---|
| **PowerPro Settings** (single) | approval threshold, warranty years, fees, SLAs, telephony numbers |
| **Property** | the place work is done; panel, utility, permit jurisdiction, access |
| **Service Request** | intake: first contact → booking; links the Call that started it |
| **Job** | the unit of work: status lifecycle, approvals, permit, warranty, job costing |
| **Visit** (+ Visit Crew) | one trip: crew, van (= warehouse), check-in/out, signature |
| **Job Photo** | tagged photos (before / after / panel / inspection…) |
| **Change Order** | written customer approval before work continues |
| **Permit** (+ Permit Inspection) | permit and its inspections |
| **Call** | one Twilio call, matched to Customer / Service Request by phone |

Custom fields on standard DocTypes (all prefixed `pp_`):

- `pp_job` on Stock Entry, Material Request, Purchase Order, Purchase Receipt,
  Purchase Invoice, Sales Invoice, Timesheet, Project — **this is job costing**.
- `pp_jobber_id` + `pp_is_mirror` on Customer, Address, Contact, Quotation, Sales
  Invoice — idempotent mirroring from Jobber; mirrored records are read-only for
  humans (`powerpro.utils.guard_mirror`).
- `pp_phone_e164` on Contact and Customer — the key calls and SMS are matched on.
- Quotation: owner approval, customer approval/signature, lost reason, links to
  Service Request and Property.
- Vehicle: `pp_warehouse` (van stock). Employee: license number/state/expiry.

Roles (created on install): `PP Owner`, `PP Dispatcher`, `PP Estimator`,
`PP Field Tech`, `PP Shop`, `PP Bookkeeper`, `PP Integration` (API only).
Give people the matching ERPNext roles too (Stock User, Sales User, Accounts User…).

Report: **Job Costing** (quoted vs invoiced vs materials / direct purchases / labor).

## Business rules implemented

- Job / Quotation above `owner_approval_threshold` (default $5,000) or on a
  commercial property needs owner approval; a PP Owner saving it approves it.
- A Job cannot go *In progress* without that approval.
- Completing a Job stamps `completed_on` and `warranty_until` (+5 years).
- A Change Order is *Approved* only with a date **and** written evidence.
- Permit with a passed Final inspection becomes *Final* and writes back to the Job.
- Missed inbound call (No answer / Voicemail) opens a Service Request unless an open
  one for that phone exists within `missed_call_dedupe_days`.
- Submitting Stock Entry / Purchase Invoice / Timesheet / Sales Invoice / Payment
  Entry with a `pp_job` re-computes the Job's actuals in the background.

## API for n8n

Create a user with role **PP Integration** (plus Sales User / Stock User for
mirrored ERPNext docs), generate API key + secret, call with header
`Authorization: token KEY:SECRET`.

```
POST /api/method/powerpro.api.log_call
  {call_sid, direction, status, received_at, from_number, to_number,
   tracking_number, source_label, duration_sec, recording_url, transcript, raw}

POST /api/method/powerpro.api.log_sms
  {sid, direction, from_number, to_number, body, received_at}

POST /api/method/powerpro.api.upsert
  {doctype, key_field, key_value, values}      # e.g. Customer by pp_jobber_id
```

Standard REST (`/api/resource/<DocType>`) works for everything else.

## Install on a bench

```bash
bench get-app https://github.com/<you>/powerpro-erp
bench --site erp.powerprofessor.co install-app powerpro
bench --site erp.powerprofessor.co migrate
```

Developer mode on the dev site (`bench --site dev.erp.powerprofessor.co set-config developer_mode 1`)
lets you change DocTypes in the UI and have them exported back into this app.

## Layout

```
powerpro/
  hooks.py            events, fixtures, scheduler
  install.py          roles
  utils.py            phone normalisation, customer lookup, mirror guard
  costing.py          refresh_job_costs
  api.py              n8n endpoints
  tasks.py            daily housekeeping
  overrides/          hooks on standard DocTypes (Contact, Customer, Quotation, costing)
  fixtures/           role.json, custom_field.json
  powerpro/           the "PowerPro" module: doctype/, report/, workspace/
```

Conventions: every custom field is `pp_*`; every DocType has `jobber_*_id` +
`is_mirror` if it can be mirrored; nothing is deleted on uninstall of data —
`bench --site <site> uninstall-app powerpro` drops the tables, so back up first.
