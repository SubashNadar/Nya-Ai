# ADR 0011: Razorpay test mode with manual advocate payouts

- **Date:** 2026-07-18
- **Status:** Accepted

## Context

Paid consultations (₹500, the advocate keeps 70%) need real payment flows for the demo without
handling card data.

## Decision

Razorpay hosted Checkout with test keys; signatures and webhooks are verified on the server.
Advocate payouts are settled by hand from `lawyer_share` (Razorpay Route is not used). Missing keys
return 503 from the payment endpoints only.

## Consequences

No card data touches Nya-AI. Payouts are a manual step until Route is enabled.

## References

DECISIONS.md "Real Razorpay integration"; `backend/app/services/payments.py`
