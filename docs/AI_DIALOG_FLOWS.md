# AI Dialog Flows

## Project
Tours_BOT

## Purpose
Describe the practical dialog flows for the AI assistant in group, private chat, Mini App support, waitlist, handoff, multilingual routing, and content-adjacent scenarios.

These flows are design references and behavior contracts.
They are not a substitute for the booking engine, payment system, or admin logic.

---

# 1. Group -> Private Flow

## Goal
Warm up the user in group chat and move them into private booking flow.

## Trigger examples
- “How much is it?”
- “Are there seats left?”
- “I want 2 seats”
- “When do you leave?”
- “Do you pick up from Timisoara?”
- “I want to go”

## Expected behavior
1. Answer briefly
2. Use verified info only
3. Provide CTA to private chat or Mini App
4. Do not ask for sensitive/private details in group

## Example flow
User:
How much is the Belgrade trip?

Assistant:
The Belgrade trip on [date] is [price] and currently has [availability if confirmed]. I can help you choose and reserve seats in private chat.

## Group CTA variants
- “Write to me in private and I’ll help you reserve seats.”
- “Open the Mini App to see details and availability.”
- “I can help you choose the best option in private chat.”

---

# 2. Private Chat -> Tour Selection Flow

## Goal
Understand the user’s need and propose relevant tours.

## Inputs to collect
- date or weekend preference
- destination or category
- budget (if relevant)
- seat count
- boarding point/city

## Rules
- ask one question at a time
- do not ask unnecessary questions
- propose 1–3 options only
- keep language concise

## Example flow
Assistant:
What date are you planning for?

User:
This weekend.

Assistant:
Got it. Do you already know the destination, or would you like suggestions?

User:
Suggestions.

Assistant:
I found 3 relevant options for this weekend:
1. [tour A]
2. [tour B]
3. [tour C]

Which one would you like to see first?

---

# 3. Tour Selection -> Reservation Flow

## Goal
Move the user from interest to temporary reservation.

## Required data before reservation
- selected tour
- number of seats
- boarding point
- language confirmed if needed

## Example flow
Assistant:
I can reserve 2 seats for you temporarily. Which boarding point would you prefer?

User:
Timisoara.

Assistant:
Perfect. I can hold 2 seats from Timisoara for a limited time while you complete payment.

Would you like me to create the reservation now?

---

# 4. Reservation -> Payment Flow

## Goal
Explain the time-limited reservation and guide user to payment.

## Rules
- make reservation window clear
- do not claim payment success before confirmation
- explain what happens if timer expires

## Example flow
Assistant:
Your seats are now reserved temporarily until [time/date].

To confirm your booking, please complete full payment before the reservation expires.

Next step:
- open Mini App
or
- continue to payment

---

# 5. Payment Pending / Expiry Flow

## Goal
Handle unpaid reservation safely.

## Example flow
Assistant:
Your reservation is still active, but it expires soon.

If payment is not completed before [time], the seats will be released automatically.

Would you like to continue to payment now?

## If reservation expires
Assistant:
The reservation has expired and the seats were released.

I can:
- create a new reservation if seats are still available
- suggest another tour
- add you to the waitlist if needed

---

# 6. No Seats -> Waitlist Flow

## Goal
Offer recovery path when a tour is unavailable.

## Example flow
Assistant:
There are no confirmed seats available for this tour right now.

I can help in one of these ways:
1. add you to the waitlist
2. suggest a similar tour
3. suggest another date

What would you prefer?

## Waitlist acceptance
Assistant:
You’ve been added to the waitlist for [tour/date].

If seats become available, we’ll notify you.

---

# 7. Payment Issue -> Handoff Flow

## Goal
Escalate payment issues safely.

## Trigger examples
- user says payment failed
- user says they paid but system shows unpaid
- webhook mismatch
- payment status unclear

## Example flow
Assistant:
I need to check this with a human operator to avoid giving you incorrect payment information.

I’m forwarding your case now so it can be reviewed.

---

# 8. Discount / Custom Request -> Handoff Flow

## Goal
Escalate non-standard commercial requests.

## Trigger examples
- “Can I get a discount?”
- “We are 8 people”
- “Can you pick us up from another place?”
- “Can you make a custom route?”

## Example flow
Assistant:
This request needs a human operator because it involves custom conditions.

I’m creating a support request now so someone can continue with you.

---

# 9. Complaint / Negative Escalation Flow

## Goal
De-escalate and hand off cleanly.

## Rules
- do not argue
- do not defend the system excessively
- acknowledge issue
- route to human

## Example flow
Assistant:
I’m sorry this caused frustration.

This should be handled by a human operator so your case can be reviewed properly.
I’m forwarding the conversation now.

---

# 10. Language Selection / Fallback Flow

## Goal
Handle multilingual routing safely.

## When language is unclear
Assistant:
I can continue in your preferred language.
Please choose:
- Romanian
- Russian
- Serbian
- Hungarian
- Italian
- German
- English

## Fallback rule
If content is missing in the selected language:
- use defined fallback language
- keep the user informed if necessary
- avoid mixing multiple languages in one confusing reply

---

# 11. Mini App Entry Flow

## Goal
Guide users from chat to Mini App naturally.

## Example flow
Assistant:
You can continue in the Mini App to:
- view tour details
- choose seats
- select boarding point
- pay securely
- track your booking

Would you like to open it now?

---

# 12. Mini App Support Flow

## Goal
Help users understand what to do in Mini App.

## Example flow
User:
I opened the Mini App. What now?

Assistant:
You can now:
1. browse available tours
2. open a tour card
3. select seats and boarding point
4. reserve temporarily
5. complete payment

If you get stuck, tell me what step you’re on.

---

# 13. Group Booking Flow

## Goal
Detect larger booking and escalate when needed.

## Example flow
User:
We want 7 seats for Saturday.

Assistant:
This should be handled with a human operator so your booking can be managed properly.

I’m creating a request now and someone will continue with you.

---

# 14. Post-Booking Confirmation Flow

## Goal
Reassure user after successful payment.

## Example flow
Assistant:
Your payment has been confirmed and your booking is now active.

Next, you will receive:
- booking confirmation
- pre-departure information
- departure-day reminder

If you need help before the trip, I’m here.

---

# 15. Pre-Departure Reminder Flow

## Goal
Prepare user for departure.

## Example flow
Assistant:
Reminder for your upcoming trip:
- destination: [tour]
- departure date/time: [value]
- boarding point: [value]

Please make sure to arrive on time.
If you have a problem, contact support as soon as possible.

---

# 16. Human Request Flow

## Goal
Respect user request for human help.

## Example flow
User:
I want to speak to a person.

Assistant:
Of course. I’m forwarding your request to a human operator now.

---

# 17. Unsupported Request Flow

## Goal
Handle questions outside scope safely.

## Example flow
Assistant:
I can help with tours, reservations, payment flow, waitlist, and booking support.

For this request, I may need to connect you with a human operator.

Would you like me to do that?

---

# 18. Admin Content Draft Flow

## Goal
Support content generation from a tour source.

## Example flow
Admin:
Generate a Telegram post and Instagram caption for this tour in Romanian and English.

Assistant:
I can prepare:
- Telegram post
- Instagram caption
- CTA variants
- “last seats” variant

Would you like standard tone or stronger sales tone?

---

# 19. Flow Design Principles

All dialog flows should follow these principles:
- short and clear
- one step at a time
- no invented facts
- use system data where available
- escalate when needed
- preserve context
- keep the next action obvious

---

# 20. Minimum Flow Coverage For MVP

The MVP must support these flows:
- group warm-up to private
- private tour selection
- reservation creation
- reservation expiry
- payment guidance
- no seats -> waitlist
- human handoff
- multilingual routing
- Mini App entry/support