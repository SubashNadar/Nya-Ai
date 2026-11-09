# Nya-AI: prompts for Lovable

Paste **Prompt 1** into a new Lovable project first. When it has built, paste Prompts 2 to 5 one at a
time; each adds one area so Lovable doesn't drop details. Fix anything off between prompts before moving
on.

---

## Prompt 1: master prompt (foundation, design system, shell, sign-in)

```
Build "Nya-AI", a professional legal-information web app for India. Free, cited answers from Indian
bare acts (BNS, BNSS, BSA and the old IPC), plus paid ₹500 video/phone consultations with verified
advocates. Two roles: a citizen (user) and an advocate. It must feel like a calm, premium legal
instrument: precise, trustworthy, quiet. Not a generic chatbot, not a SaaS dashboard template.

TECH
React + TypeScript + Vite, Tailwind CSS, shadcn/ui as the base (restyled, never default-looking),
lucide-react icons (1.5px stroke), framer-motion for motion, react-router. Use mock data in
src/data/*.ts with typed interfaces in src/types.ts so a real API can be plugged in later. No backend.

DESIGN LANGUAGE: "PARCHMENT & INK" (light, default)
- Mood: a well-made law book in daylight. Warm ivory paper, deep navy ink, brass details.
  Editorial typography, lots of air. Bright and calm, never stark white or clinical.
- Colours (define as CSS variables and Tailwind tokens; use nothing else):
  --bg #FAF7F0 (page, warm ivory), --surface #FFFFFF (cards), --soft #F3EEE3 (soft sections, hovers),
  --well #EEE8DB (inset panels and form fields), --line #E6DFD1 (1px borders),
  --ink #1C2430 (text, deep navy ink), --body #3A4452, --muted #5B6472, --faint #6F7785,
  --primary #1F3A5F (primary buttons: navy with white text; hover #2A4B78),
  --brass #A8792E (accents, citations, focus ring, active states), --brass-text #7D5A20 (brass text
  on ivory, for contrast), --brass-tint #F3E7CF (pale brass highlight),
  success #2F7D5B on #E5F2EB, warning text #8A5A12 on #FBF1DE, danger #C0392B, info #1D6FA5.
  Navy is the action colour (one primary button per screen); brass is the detail colour (citations,
  focus, small labels, the italic key word in headings). Never fill large areas with brass.
- Optional dark mode (a toggle in Account, off by default): the "Orbit" navy theme with page #0A1424,
  cards #0F1E33, text #F3F5F9, brass #D9B56E as the primary colour and a faint brass grid. Build all
  colours as CSS variables so the toggle only swaps variable values.
- Background: plain warm ivory, no grid, no glow. Cards are white with soft, diffuse shadows
  (0 6px 20px -8px rgba(28,36,48,0.10)) and a 1px --line border. The only dark surfaces are the
  sign-in hero panel and the orb-menu overlay, which use the navy theme on purpose.
- Typography (Google Fonts): Fraunces for headings (optical size on, weight 500–600, slight negative
  tracking), Figtree for body and UI (15px base, 1.6 line height), JetBrains Mono for metadata,
  section numbers, citations, dates, refs and timers (12–13px, letter-spacing 0.02em, often uppercase).
  Headings are sentence case. Large display headings may set one key word in italic Fraunces brass.
- Shape: 14px radius on cards, 10px on inputs and buttons, full pills for chips and toggles. 1px
  --line borders plus soft diffuse shadows on cards; stronger shadows only on floating layers.
- Spacing: 8px grid, generous. Max content width 1200px; reading width 720px for answers.
- Icons: lucide, 18px, never in coloured circles.

SIGNATURE COMPONENTS (build these as reusable components in src/components/, they define the style)
1. OrbMenu: the app has NO sidebar and NO bottom tab bar. A slim 56px top bar holds, on the left, the
   logo: a 28px brass orb (radial gradient brass to brass-dark with a thin cream orbit ring around it)
   and the wordmark "Nya-AI" in Fraunces; in the centre, the current section in mono as "§ ASK", "§ MY
   MATTERS", etc.; on the right, the user avatar. Tapping the orb dims the page (navy 70% + blur) and
   fans the sections out along a circular orbit around the orb, each as a pill with an icon and label,
   staggered 40ms. User sections: Ask, My matters, Advocates, Consultations, Account. Advocate sections:
   Dashboard, Review queue, Messages, Law library, Profile. Small text links under the orbit: Legal,
   About, Help, Contact. Esc, tapping outside or choosing an item closes it. Keyboard accessible
   (arrow keys move around the orbit, focus is trapped while open). On phones the orbit becomes a
   vertical arc on the left edge.
2. CitationChip: inline mono chip like "BNS §303" with a brass hairline border; hover/focus opens a
   popover with the section heading, the first lines of the section text, the page number and "Open
   source". Every legal claim in the UI links to one.
3. ParagraphAnswer: an answer block where each paragraph has a brass "¶1", "¶2" marker in the left
   margin (mono), a numbered sources list at the bottom, and a confidence meter (see 5).
4. TraceRail: a thin vertical rail of the agent's real steps (Guard → Temporal → Router → Statute
   researcher / SQL lookup → Writer → Critic → Advocate review), each a small node with status (done
   = brass dot, running = pulsing ring, skipped = hollow). Collapsible. It reveals "how the answer was
   made" without showing internals.
5. ConfidenceMeter: three short brass bars (Low / Medium / High) plus a mono label, with a tooltip
   explaining it is based on how well the cited sections support the answer.
6. JurisdictionSwitch: shows which law applies, given the incident date: a horizontal line split at
   "1 JULY 2024" with "IPC · CrPC · Evidence Act" on the left and "BNS · BNSS · BSA" on the right; a
   brass pin marks the incident date and the side that applies lights up.
7. DeadlineClock: a circular ring timer (SVG) for a limitation period (e.g. "Cheque bounce notice: 30
   days"), filled in brass as time passes, turning warning-amber under 25% left and danger-red under
   10%, with the due date in mono and the governing section as a CitationChip.
8. StatusBadge: pill badges in mono uppercase: ANSWERED, PENDING REVIEW, REVIEWED, EMERGENCY, BASIC MODE.
9. Empty, loading and error states for every list: loading = shimmering skeleton rows in --raised; empty
   = one line of Fraunces plus a single brass action; error = plain sentence and "Try again".

MOTION
Purposeful and quiet: 180–240ms ease-out. Route change = fade + 8px rise. Lists stagger in (30ms).
Primary buttons get a soft sheen on hover and press to 0.98. Cards get a soft spotlight that
follows the pointer and a brass border on hover. The chat composer has a thin conic brass border that
slowly rotates while the agent is working. Respect prefers-reduced-motion: turn all of it off.

ACCESSIBILITY AND QUALITY
WCAG AA contrast (use --brass-text, not --brass, for brass-coloured text on ivory), visible 2px brass focus ring, every
control reachable by keyboard, aria labels on icon buttons, 44px touch targets, no text in images.
Fully responsive: 360px phones up to 1440px desktops; design phone and desktop deliberately, not by
shrinking.

CONTENT RULES (important, this is a legal product)
- Nya-AI gives legal information, never legal advice. A persistent one-line footer note on answer
  screens: "Legal information from Indian bare acts. Not legal advice. For your own case, speak to an
  advocate."
- Never show invented statistics, case outcomes, win rates or percentages of success.
- Citations always as "ACT §NUMBER" (e.g. "BNS §303(2)"). Dates in Indian format "12 March 2024".
  Money as "₹500".
- Plain, warm, short sentences. No legal jargon without a one-line explanation.

BUILD NOW
1. The design system: tokens, fonts, the grid background, and the components above with a /styleguide
   route that shows every component in all its states.
2. The app shell with OrbMenu and route transitions.
3. Sign-in (/login): a split layout. Left (desktop only): a large Fraunces headline "Know the law that
   applies to *you*." with "you" in brass italic, a short subline, and an animated JurisdictionSwitch
   demo. Right: a card with a sliding pill toggle "I need legal help" / "I'm an advocate", a phone
   number input with +91 prefix, "Send code", then a 4-box OTP input (any 4 digits work in this mock)
   and "Continue as guest". Link to Legal and Privacy under the card.
4. Public pages (/legal, /about, /help, /contact) in a calm editorial reading layout, using placeholder
   copy clearly marked [DRAFT].
Then stop and show me.
```

---

## Prompt 2: Ask (the chat)

```
Now build the Ask screen (/chat), the heart of the app. Keep every design rule from before.

Layout (desktop): three zones. Centre: the conversation at reading width (720px). Right: a 320px
"Context" panel with the JurisdictionSwitch for this question and the TraceRail. Left: nothing (the
OrbMenu handles navigation); a "New question" pill and a short list of recent conversations sit at the
top of the conversation area. Phone: conversation only; Context opens as a bottom sheet from a
"How this was answered" link under each answer.

Empty state: a centred Fraunces greeting "What happened?", a one-line subline, and four starter cards
in a 2×2 grid (spotlight hover): "Someone stole my phone", "A cheque I received bounced", "What does BNS
§303 say?", "Police haven't registered my FIR". Each starts a question.

Composer: a large rounded input that grows to 6 lines, with a send button (navy), a mic icon (disabled,
tooltip "Coming soon"), and below it a "When did it happen?" date chip that opens a date picker; once
set it shows "Incident: 12 March 2024" and updates the JurisdictionSwitch live (IPC side before 1 July
2024, BNS side from then). While the agent works, the composer border rotates and the TraceRail
animates step by step (simulate ~2.5s with timeouts).

User message: right-aligned, --raised background, plain text, time in mono.
Assistant answer: ParagraphAnswer with 2–4 paragraphs, CitationChips inline, numbered sources, the
ConfidenceMeter, a StatusBadge, and a row of quiet actions: copy, thumbs up/down (down opens a small
"What was wrong?" popover with reasons), "Ask an advocate" (secondary brass outline button that goes
to /plan with the question prefilled).

Special answer states (make mock conversations for each):
- EMERGENCY: a full-width danger-tinted card at the top with helplines as large tap targets (112
  Police, 181 Women, 1098 Child, 14416 Mental health) and the line "If you are in danger, call now."
  No legal text above it.
- PENDING REVIEW: the answer is blurred behind a frosted panel: "An advocate is checking this answer
  because it concerns a live matter. You'll be notified." with a small clock and queue position.
- BASIC MODE: a thin warning strip "The law library is offline. This is a simpler answer from basic
  rules." above a shorter answer without citations.
- REFUSED: a calm card explaining Nya-AI can't help with that request and why, with a link to Help.

Use realistic mock content: e.g. "My phone was stolen on 12 March 2024" answers with IPC §378 (Theft) and
IPC §379 (Punishment for theft) because the incident is before 1 July 2024; the same question dated
1 August 2024 cites BNS §303(1) and §303(2).
```

---

## Prompt 3: My matters (dashboard) and the consultation flow

```
Build the user's dashboard and the consultation flow.

/dashboard "My matters":
- A header row of three figures with count-up animation, each a quiet card: "Questions asked",
  "Clocks running", "Next consultation" (date in mono, or "None booked").
- The Statute Timeline: a full-width horizontal timeline from 2023 to today, split by a brass vertical
  rule labelled "1 JULY 2024 · NEW CRIMINAL LAWS". Each question with an incident date is a node placed
  on its date (IPC side or BNS side); hovering shows the question and its main citation; clicking opens
  the conversation. Questions without a date sit as chips in an "Undated" tray under the line. On
  phones the timeline becomes vertical.
- "Clocks running": a row of DeadlineClocks (e.g. "Cheque bounce: demand notice, 30 days, NI Act
  §138(b)", "RTI first appeal, 30 days, RTI Act §19(1)", "Consumer complaint, 2 years, Consumer
  Protection Act §69"). Each shows days left, the due date and a note "Counted from the incident date
  you gave. Check with an advocate."
- "Next consultation" card with the advocate's photo placeholder, name, date and time, and "Join call
  room" (enabled 10 minutes before).

/lawyers "Advocates": a filter bar of sliding pills (All, Criminal, Family, Consumer, Cyber, Property)
and a language select; a grid of advocate cards (initials avatar with brass ring, name in Fraunces,
"Verified" badge with Bar Council ID in mono, practice areas as chips, languages, years of practice,
"₹500 · 30 min", "Book"). No star ratings or win rates.

/plan "Plan your consultation": a two-column form (stacks on phone): Topic, Facts in order (textarea with
a gentle character guide), Questions for the advocate (add/remove list, up to 5), Goals (up to 3),
Documents to keep ready (checklist). A "Draft from my conversation" button fills it with mock content and
a shimmer while drafting. Right side: a live preview of the brief as the advocate will see it, on a
cream paper card with Fraunces headings. Then "Choose an advocate".

/booking/:lawyerId: a date strip (next 14 days, horizontal scroll) and time slots as pills; a summary
card (advocate, slot, ₹500, "Advocate receives ₹350"). /pay/:bookingId: an order summary and a "Pay ₹500"
button that opens a mock Razorpay-style modal (clearly labelled TEST MODE), then /success/:bookingId with
a calm confirmation, the booking ref "NX-20261109-001" in mono, an "Add to calendar" button and next steps.

/bookings "Consultations": upcoming and past tabs (sliding pill); each row shows advocate, date, status
badge (PENDING PAYMENT, CONFIRMED, COMPLETED, CANCELLED) and actions.

/call/:bookingId "Call room": the agenda from the brief on the left, a large centre panel that says
plainly "Your advocate will phone you at the booked time" with a countdown, and on the right private notes
(stored only on this device, said so).
```

---

## Prompt 4: the advocate side

```
Build the advocate side (shown after signing in with "I'm an advocate"). Same design system; the OrbMenu
shows the advocate sections.

/portal "Dashboard": figures (Today's consultations, Answers waiting for review, This month's earnings
in ₹ with the 70% share explained in a tooltip). "Today" list of consultations with the client's brief
one click away. A "Review queue" preview with the oldest waiting answers first.

Review queue (/portal#reviews or a tab): each item shows the user's question (personal details masked as
[PHONE], [AADHAAR]), why it was held ("Live matter: person in custody"), the agent's draft as a
ParagraphAnswer with its citations, the retrieved sections side by side, and a decision bar: Approve,
Edit (opens the draft in an editor with citation chips preserved), Reject with a note (offers the user a
consultation). After a decision show a toast and an entry in a small audit list (who, what, when, in mono).

/messages: a two-pane inbox (threads list, conversation), unread dots in brass, mark-as-read on open.

/library "Law library" (advocates only): readiness checks as a row of status tiles (Database, Azure key,
PDFs present, Langfuse), each green/amber/red with a one-line reason. A pipeline view of ingestion stages
as connected nodes (Fetch → Parse → Split → Embed → Index → Eval) showing counts per act. An acts table
(Act, Sections, Nodes, Last ingested, Status) with checkboxes and "Ingest selected". A "Test retrieval"
box: a question plus an "as of" date, returning ranked sections with score, found-by (vector / text /
exact) and page. Mock data: BNS 358 sections / 380 nodes, BNSS 531 / 547, BSA 170 / 178, IPC 555 / 566.

/profile: advocate profile editor with a live preview of their public card.
```

---

## Prompt 5: polish pass

```
Polish pass across the whole app, without changing layouts:
1. Check every screen at 360px, 768px, 1024px and 1440px; fix overflow, wrapping, tap targets.
2. Keyboard-test every flow; ensure the brass focus ring is visible everywhere and the OrbMenu traps
   focus correctly.
3. Contrast-check brass and muted text on ivory and white; use --brass-text for small brass text.
4. Add skeleton, empty and error states anywhere they are missing.
5. Make sure every legal reference uses CitationChip, every date is "12 March 2024" format, money is
   "₹500", and the "Not legal advice" note is on every answer screen.
6. Remove anything that looks like a default shadcn or template component: every card, input, tab and
   button must use the Orbit tokens.
7. Verify prefers-reduced-motion disables all animation.
8. Update /styleguide with every component and state.
```

---

## Tips for using these with Lovable

- Attach 1–2 screenshots of the current app (or the Orbit canvas) with Prompt 1 as visual reference.
- If Lovable drifts to generic styling, reply: "Re-apply the Parchment & Ink design system from the
  first prompt: ivory page #FAF7F0, white cards with soft shadows, navy ink text #1C2430, navy #1F3A5F
  for the single primary button, brass #A8792E for citations and focus, Fraunces headings, JetBrains
  Mono for citations and dates, 1px #E6DFD1 borders, no default shadcn look."
- Ask for one screen at a time if a prompt gets partially built.
- The real API contract is in `backend/app/api/schemas/` and `frontend/src/types.ts`; ask Lovable to
  keep the mock data shapes matching those when you connect it.
