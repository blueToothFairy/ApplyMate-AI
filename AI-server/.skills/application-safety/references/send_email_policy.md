# Send Email Policy

Before ExpressJS sends an email, it must call `/ai/validate-send`.

Validation passes only if:

- approval_status is approved.
- approval_id matches.
- recipient matches approved draft.
- subject matches approved draft.
- body matches approved draft.
- attachment version matches approved CV.
- no unresolved placeholder exists.

The AI server never sends email directly in the MVP.
