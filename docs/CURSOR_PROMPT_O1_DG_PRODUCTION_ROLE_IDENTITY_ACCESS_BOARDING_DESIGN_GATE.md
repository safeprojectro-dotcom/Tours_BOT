# CURSOR_PROMPT_O1_DG_PRODUCTION_ROLE_IDENTITY_ACCESS_BOARDING_DESIGN_GATE

You are continuing the existing Tours_BOT project.

This is NOT a new project, NOT a rewrite, and NOT a new roadmap.

## Cursor mode

Agent

## Block

O1-DG — Production Role, Identity, Access, Supplier/Driver Operations & Boarding Design Gate

## Execution mode

Docs-only functional block / design gate.

Reason:
- This block defines production identity, access, supplier/driver operations, vehicle/device assignment, ticket/QR and boarding validation architecture.
- It is a design gate before any code, migrations, endpoints, QR tokens, passenger manifest, or driver scan implementation.
- This belongs under P0 → O1: Order / Ticket QR & Boarding Validation.
- It must not create a new unrelated roadmap branch.

---

## Context

P0 already exists and remains the operational roadmap layer on top of the MVP implementation plan and supplier marketplace plan.

P0 states:
- `IMPLEMENTATION_PLAN.md` remains the baseline MVP plan.
- P0 sits above it and addresses operational complexity.
- O1 is the planned future block for Order / Ticket QR & Boarding Validation.
- Secure QR / order / ticket / boarding QR belongs to O1.
- Marketing QR belongs to M1 and must not be mixed with secure ticket/boarding QR.
- Passenger manifest, QR security, auth/permissions, public side effects and personal data are dangerous areas and must be designed/narrow-scoped.

Recent implemented/demo context:
- S1C supplier notification outbox/delivery foundation exists.
- S1D operational sales push preview/publish exists.
- DEMO-1 physical Telegram demo smoke playbook exists.
- Now the project needs production design for:
  - customer access;
  - supplier access;
  - driver access;
  - admin/super admin access;
  - vehicle/device identity;
  - departure assignment;
  - passenger manifest;
  - ticket/QR;
  - driver boarding validation;
  - trip closeout report.

---

## Goal

Create a production design gate document that answers:

1. How customers, suppliers, drivers, admins and super admins authenticate.
2. How roles are assigned and revoked.
3. How supplier organizations manage offers, vehicles, drivers and trips.
4. How drivers access only assigned departures.
5. How service phones / vehicle devices work.
6. How tickets and QR should be modeled later.
7. How boarding validation should work.
8. What supplier sees vs driver sees vs customer sees vs admin sees.
9. How trip completion report should work.
10. What should be implemented first after this design gate.

This is a design document only.

---

## Required new document

Create:

```text
docs/O1_PRODUCTION_ROLE_IDENTITY_ACCESS_BOARDING_DESIGN_GATE.md