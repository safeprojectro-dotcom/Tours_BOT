# Testing Strategy

## Goal
Ensure safe incremental development for the Tours_BOT project.

## Priority areas
- booking creation
- reservation expiration
- payment status changes
- waitlist behavior
- multilingual fallback
- handoff triggers
- admin tour management
- Mini App booking flow

## Test levels

### Unit tests
Use for:
- business rules
- booking logic
- status transitions
- payment state mapping
- waitlist queue behavior

### Integration tests
Use for:
- API endpoints
- database interactions
- payment webhook handling
- reservation expiration workers
- Telegram flow critical transitions

### Manual checks
Use for:
- Telegram group behavior
- private chat UX
- Mini App screens
- multilingual display quality
- admin approval and publishing flow

## Rule
For every non-trivial feature:
1. define affected modules
2. define risks
3. define minimal tests
4. implement smallest safe step
5. verify manually and/or automatically
