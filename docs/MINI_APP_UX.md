# Mini App UX

## Project
Tours_BOT

## Purpose
Define the UX structure for the Tours_BOT Mini App before full implementation.

This document exists to prevent chaotic UI implementation and to make screen flow, CTA hierarchy, states, and support paths explicit before full coding.

---

## 1. UX Principles

The Mini App must be:
- mobile-first
- simple
- conversion-oriented
- multilingual-ready
- clear in next-step guidance
- consistent with booking and payment logic
- supportive of handoff/help flows

The Mini App must not:
- overload the user with too many choices
- hide the booking timer
- duplicate backend/business logic in UI
- confuse the user with weak CTA hierarchy

---

## 2. Main User Goals

Users should be able to:
1. browse tours
2. view tour details
3. reserve seats
4. complete payment
5. check booking status
6. join waitlist if needed
7. get help or human assistance

---

## 3. Screen Map

Recommended MVP screen map:

1. Home / Catalog
2. Filters / Search
3. Tour Details
4. Reservation
5. Payment
6. My Bookings
7. Waitlist / Alternative Option State
8. Language / Settings
9. Help / Contact Operator

---

## 4. Screen Details

## 4.1 Home / Catalog
Purpose:
- show available tours quickly
- guide users toward details or booking

Should show:
- tour card image
- title
- date
- short duration label
- price
- availability label if appropriate
- status badge if useful
- CTA: Details
- CTA: Reserve

Key UX rule:
The user should understand available options in a few seconds.

---

## 4.2 Filters / Search
Purpose:
- narrow down tours by intent

Potential filters:
- date
- destination
- category
- budget
- duration
- language if relevant for content display

Key UX rule:
Filters must help, not overwhelm.

---

## 4.3 Tour Details
Purpose:
- help the user decide whether to book

Should show:
- gallery
- title
- destination
- departure date/time
- return date/time
- price
- remaining availability if confirmed
- description
- included / excluded
- boarding points
- policy summary
- CTA: Reserve
- CTA: Ask for help

Key UX rule:
Tour details should answer decision-making questions without becoming a wall of text.

---

## 4.4 Reservation
Purpose:
- convert interest into temporary reservation

Should allow:
- select number of seats
- choose boarding point
- confirm reservation
- see reservation timer clearly
- understand what happens next

Must show:
- selected tour summary
- selected date
- seat count selector
- boarding point selector
- reservation timer
- CTA: Confirm Reservation
- CTA: Back

Key UX rule:
Reservation must feel safe and clear, not confusing.

---

## 4.5 Payment
Purpose:
- guide user to full payment for confirmation

Should show:
- booking summary
- amount
- timer / reservation expiry awareness
- CTA: Pay Now
- payment status feedback
- CTA: Contact Support if needed

Key UX rule:
Never make the user guess whether payment is pending, complete, or failed.

---

## 4.6 My Bookings
Purpose:
- let users understand current booking state

Should show:
- active reservations
- confirmed bookings
- canceled items
- waitlist status
- payment status
- CTA to open details
- CTA to contact support

Key UX rule:
Booking status must be understandable at a glance.

---

## 4.7 Waitlist / Alternative Option State
Purpose:
- avoid dead-end when no seats are available

Should show:
- no seats available message
- CTA: Join Waitlist
- CTA: View Similar Tours
- CTA: Another Date
- CTA: Contact Support if needed

Key UX rule:
“No seats” must not become the end of the journey.

---

## 4.8 Language / Settings
Purpose:
- control language and basic app preferences

Must support:
- language selection
- language persistence
- return to main UX flow

---

## 4.9 Help / Contact Operator
Purpose:
- provide safe escalation path

Should allow:
- ask for human support
- display support/help instructions
- explain what kind of help is available

Key UX rule:
Help entry must be visible, but not dominate the booking flow.

---

## 5. CTA Hierarchy

Primary CTA:
- Reserve
- Pay Now

Secondary CTA:
- Details
- View Booking
- Join Waitlist

Support CTA:
- Contact Operator
- Help
- Change Language

Rules:
- one primary CTA per main screen
- avoid multiple competing primary actions
- help CTA should be available but secondary
- payment CTA should be dominant on payment-relevant screens

---

## 6. Loading States

Need explicit loading states for:
- catalog load
- tour details load
- reservation creation
- payment session creation
- booking status retrieval
- waitlist action
- help/handoff submission

Rules:
- user must know something is happening
- prevent duplicate actions during critical transitions
- show short meaningful loading text where useful

---

## 7. Empty States

Need explicit empty states for:
- no tours found
- no bookings
- no waitlist items
- no matching filters

Each empty state should provide a useful next action, such as:
- clear filters
- browse all tours
- contact support
- return to catalog

---

## 8. Error States

Need explicit error states for:
- failed catalog load
- failed details load
- reservation creation failure
- payment initiation failure
- booking retrieval failure
- waitlist failure
- Mini App support issue

Rules:
- explain simply
- do not expose raw technical errors to user
- give a recovery path
- provide help CTA where needed

---

## 9. Reservation Timer State

This is critical.

The reservation timer must be:
- visible
- understandable
- updated correctly
- tied to reservation logic, not guessed in UI

The user must understand:
- reservation is temporary
- expiration time
- what happens after expiration
- what action is needed before expiration

---

## 10. Help / Handoff Entry Points

Help/handoff should be available from:
- tour details
- reservation
- payment
- my bookings
- error states when relevant

Triggers for help CTA prominence:
- payment issue
- custom request
- confusion
- no suitable options
- no seats available
- repeated failure state

---

## 11. Multilingual UX Rules

The Mini App must:
- render in the selected/detected language
- use fallback language rules
- avoid mixed-language confusion
- preserve booking clarity regardless of language

Missing translation behavior must be graceful, not broken.

---

## 12. Mini App State Model

Key user-visible states:
- browsing
- viewing details
- reserving
- reservation active
- payment pending
- payment successful
- payment failed
- reservation expired
- waitlist joined
- support requested

This state model should be reflected in UI texts and CTA logic.

---

## 13. Manual UX Validation Checklist

Before considering Mini App UX acceptable, verify:
- catalog is readable on mobile
- tour details support decision-making
- reservation is clear
- timer is visible
- payment step is understandable
- waitlist path works
- help path is obvious
- no screen feels overloaded
- multilingual fallback is acceptable
- error recovery is understandable

---

## 14. Immediate Design Output

Before full Mini App implementation, this file should be refined with:
- final screen order
- component list
- CTA per screen
- state-specific notes
- known UI risks
