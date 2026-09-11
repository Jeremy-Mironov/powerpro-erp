# PowerPro — field service layer for ERPNext

Custom Frappe app for Power Professor LLC (Portland OR / Vancouver WA electricians).

Design rule (decided 10.09.2026): **ERPNext's own modules do their own jobs.**
The app does not add a "PowerPro" section to the UI. It extends the standard
objects and puts its own DocTypes inside ERPNext's Projects / CRM / Stock sidebars.

- **A Job is an ERPNext `Project`.** Every ERPNext transaction (Sales Invoice,
  Stock Entry, Purchase Invoice, Timesheet, Sales Order) already links to a
  Project, and Project already computes material cost, labor cost, purchases,
  billed amount and gross margin. We add the field-service fields on top.
- What ERPNext lacks (property, visit, permit, change order, call) is added as
  DocTypes that link to the Project.

Requires: Frappe 16 + ERPNext 16 (built and tested on 16.33 / 16.34).

## The Field section (v5)

A **Field** sidebar (desktop icon "Field") is the crew's and dispatcher's menu, in the
order of a working day, Jobber-style: Home · Schedule (visit calendar) · Dispatch
(kanban on visit status) · Map · Clients · Properties · Requests · Quotes · Projects ·
Visits · Invoices · Expenses · Timesheets · More (Photos, Notes, Permits, Change
Orders, Calls, Van stock, Vans, Checklist templates, Settings). It links to the
standard objects only; ERPNext's own sections stay for the office.

- **Field Note** — one note object for Customer / Property / Project / Visit with a
  type, a visibility level (Everyone / Office / Owner), pinning and a photo. Forms
  show a "Field notes" panel with the notes inherited down the chain
  (customer → property → project → visit), filtered by the viewer's role
  (`permission_query_conditions` + `has_permission`).
- **Instructions for crew** (`pp_instructions` on Project) are copied onto every visit.
- **Geocoding** — properties are geocoded on save by the US Census Geocoder (free,
  no key, US-only, returns the county) with OpenStreetMap Nominatim as fallback;
  choice in PowerPro Settings. No Google APIs: Google's terms forbid showing its
  geocoding results on a non-Google map and storing coordinates beyond 30 days.
  County → ERPNext Territory (created on demand under the state); coordinates flow
  to projects and visits → Map views (OpenStreetMap, built into Frappe). "Navigate"
  opens Google Maps in the browser by street address — no API involved.
- **Visit** — GPS at check-in / check-out (phone browser), checklist from templates
  per project type (seeded: Service call, Panel upgrade, EV charger, Safety check),
  required items block "Done", buttons Navigate / Issue materials / Transfer to van.
- **Line items** of a project = its Sales Order (made from the quotation).
- **Field Expense** — receipt photo from the field; office approves and books it as a
  Purchase Invoice against the project (feeds job costing).

## Jobber → ERPNext

| Jobber | ERPNext | Sidebar |
|---|---|---|
| Client | Customer | CRM / Selling |
| Property | **Property** (ours: panel, utility, permit jurisdiction, access, coordinates) | CRM |
| Request | **Service Request** (ours) | CRM |
| Quote | Quotation + approval / signature fields | Selling |
| **Job** | **Project** + `pp_*` fields (property, job status, lead tech, approval, warranty, permit) | Projects |
| Visit | **Visit** (ours: crew, van = warehouse, window, check-in/out, signature) | Projects, Calendar view |
| — | **Change Order**, **Permit** (+ inspections), **Job Photo** | Projects |
| Invoice | Sales Invoice | Invoicing |
| Phone call | **Call** (ours; Twilio via n8n) | CRM |

Map view: Property, Project and Visit carry `latitude` / `longitude` (named without
the `pp_` prefix on purpose — Frappe's built-in Map view looks for those names).
Kanban: make a board on `Project.pp_status`. Calendar: Visit.

## What is in the box

```
powerpro/
  hooks.py                      doc_events on Project, Quotation, Customer, Contact, Sales Invoice, Payment Entry
  install.py                    roles, Project Types, sidebar items, cleanup of v1-v3 artifacts (idempotent)
  overrides/project.py          the Job rules on Project
  overrides/quotation.py        owner approval on quotations
  api.py                        endpoints for n8n (upsert, log_call, log_sms)
  utils.py                      E.164, customer-by-phone, mirror guard
  tasks.py                      daily: Under warranty -> Closed
  public/js/project.js          Project form: buttons (Visit, Change Order, Photo, Permit, Sales Invoice), owner approval
  public/js/project_list.js     Project list: job status indicator and default filter
  powerpro/custom/*.json        customizations of standard DocTypes (fields, layout, permissions) — synced on migrate
  powerpro/doctype/*            PowerPro Settings, Property, Service Request, Visit (+Crew, +Checklist), Van, Job Photo,
                                Change Order, Permit (+Inspection), Call, Field Note, Field Expense, Visit Checklist Template
  powerpro/workspace/field      Home page of the Field section (shortcuts with counts)
  workspace_sidebar/field.json  the Field sidebar;  desktop_icon/field.json  its icon
  geo.py                        Google geocoding + county -> Territory
  notes.py                      inherited field notes for forms
  public/js/notes.js            the notes panel (app_include_js);  customer.js  client card buttons
  fixtures/role.json            PP Owner, PP Dispatcher, PP Estimator, PP Field Tech, PP Shop, PP Bookkeeper, PP Integration
deploy/                         apps.json + step-by-step install on frappe_docker
```

### Project customizations (`powerpro/custom/project.json`)

- 28 custom fields, all `pp_*` except `latitude` / `longitude`.
- Form layout via a `field_order` property setter: first tab is the job (title,
  status, type, customer, property, lead tech, schedule, scope, approval & permit,
  origin, location); ERPNext's Costing / Progress / More Info / Connections tabs stay.
- `naming_series` = `JOB-.YYYY.-`; ERPNext `status` is read-only and follows `pp_status`.
- Money fields (estimated, costing, purchases, consumed material, billed, margin,
  quoted, paid) are **permlevel 2**: PP Owner / Estimator / Integration write,
  Bookkeeper and Projects Manager read, techs and dispatch don't see them.
- Connections tab: Visits, Photos, Change Orders, Permits, Calls.

Custom DocPerm records replace ERPNext's standard permission rows for Project, so
`project.json` carries the full set (ERPNext's rows + ours).

## Business rules implemented

- Project / Quotation above `owner_approval_threshold` (default $5,000) or of type
  *Commercial project* (Quotation: on a commercial property) needs owner approval; a
  PP Owner saving it approves it.
- A Project cannot go *In progress* without that approval.
- Completing a Project stamps `pp_completed_on` and `pp_warranty_until` (+5 years).
- Submitting a Sales Invoice / Payment Entry for the Project moves it
  Complete → Invoiced → Paid (and back on cancel); `pp_paid_total` is kept current.
- A Change Order is *Approved* only with a date **and** written evidence.
- Permit with a passed Final inspection becomes *Final* and writes back to the Project.
- Missed inbound call (No answer / Voicemail) opens a Service Request unless an open
  one for that phone exists within `missed_call_dedupe_days`.
- Records mirrored from Jobber (`is_mirror` / `pp_is_mirror`) are read-only for
  humans; PP Integration and System Manager may write.

## API for n8n

Create a user with role **PP Integration** (plus Sales User / Stock User /
Projects User for mirrored ERPNext docs), generate API key + secret, call with
header `Authorization: token KEY:SECRET`.

| Method | Purpose |
|---|---|
| `POST /api/method/powerpro.api.upsert` | `doctype, key_field, key_value, values` — idempotent create-or-update by external id |
| `POST /api/method/powerpro.api.log_call` | one Twilio call → `Call` (matched to Customer by phone; missed call → Service Request) |
| `POST /api/method/powerpro.api.log_sms` | one SMS → `Communication` on the Service Request / Customer timeline |
| standard `/api/resource/<DocType>` | everything else |

## Conventions

- Custom fields on standard DocTypes: `pp_` prefix, module `PowerPro`, shipped in
  `powerpro/custom/<doctype>.json` with `sync_on_migrate: 1`.
- Our own DocTypes: module `PowerPro`, naming series `REQ- / VIS- / CO- / PRM-`,
  `PROP-#####`, `PHT-#####`; Project uses `JOB-.YYYY.-`.
- Never edit ERPNext or Frappe sources; never customize through the UI on prod —
  change the files here, `git push`, rebuild, `bench migrate` dev, then prod.
- Money on Project lives at permlevel 2; internal notes too.

## Upgrading from v1–v3 (separate `Job` DocType)

`after_migrate` removes the old `PowerPro` workspace / sidebar / desktop icon, the
`Job Costing` report, the `pp_job` custom fields and the `Job` DocType if they
exist. Sites created with v1–v3 hold no data, so a plain `bench migrate` is enough.
