# Nya-AI design

**Current theme (2026-11-06): Orbit navy and brass.** The owner chose to restore it. The colour
tokens are back to the Orbit values in `frontend/tailwind.config.js` (as at b7dbca3), and the layout
is unchanged. The Sage & Clay notes below are kept for history; they no longer describe the app.

## History: Sage & Clay (2026-10-30 to 2026-11-06)

Replaced the Orbit navy and brass theme on 2026-10-30. The owner found Orbit too aggressive and asked
for a pleasant palette. Orbit's menu, layout and alignment stay exactly as they were (trace panel,
cited ¶ answer, temporal panel, consult plan, call room, 40px grid); **only colours changed**. New
control styling or behaviour is proposed below and applied only after the owner approves it.

## Sources studied

- **Radix Colors** (MIT, https://github.com/radix-ui/colors): the sage, jade, sand and amber scales
  set the neutrals, the action colour and the warning tones, and their step 11/12 rule for text
  contrast.
- **Magic UI** (MIT, https://github.com/magicuidesign/magicui): border beam, shimmer button, magic
  card and highlighter, the basis of the proposed controls. They would be rewritten as plain CSS
  because Magic UI targets Tailwind 4 and `next-themes`, and this app is Tailwind 3.
- **shadcn/ui** (MIT): token names and the button and badge components were already in place.

## Palette

| Token (Tailwind name) | Hex | Use |
| --- | --- | --- |
| `bg` | `#F6F4EE` | warm paper page background, faint dot grid, soft jade and clay wash |
| `surface` | `#FFFFFF` | cards, panels |
| `soft`, `line`, `input` | `#EEEBE3`, `#E3DFD5`, `#D5D0C4` | quiet fills and borders |
| `ink`, `body3`, `body2`, `muted`, `faint` | `#1C2321` to `#6F7773` | text; `faint` still passes 4.5:1 on white |
| `primary` | `#1E6B5C` (jade) | actions, active nav, focus ring; white text 6.3:1 |
| `primary-tint` | `#E3F1EC` | active nav and tab pill |
| `brass` (now clay) | `#E0894A` | attention: answer edge, dots, marker, beam |
| `brass-light` (clay text) | `#A4551F` | mono labels and citation numbers; 5.4:1 on white |
| `brass-soft`, `brass-glow` | `#FCEFE3`, `#F2B184` | tinted tiles, highlights on dark panels |
| `navy-*` (now deep jade) | `#0F2E28` to `#2E6E60` | only the login hero panel |

The old token names (`navy`, `brass`) are kept so no page had to be rewritten; the comments in
`tailwind.config.js` say what each now holds.

## Proposed controls (declined 2026-10-31)

The owner chose Orbit's layout with Sage & Clay colours and none of these controls. Kept here for
reference only.

Built once in d12d908, then taken out in the next commit because the owner wants layout and
behaviour unchanged until each one is approved. The code is in d12d908 if one is approved.

1. **Beam composer**: a slow jade-to-clay light travels round the chat box; faster on focus.
2. **Tactile keys**: primary buttons look raised and sink 2px on press, with a light sweep on hover.
3. **Spotlight cards**: a soft clay glow follows the pointer on chat starter and lawyer cards.
4. **Sliding pills**: the login role switch and lawyer filters slide between options (the sidebar
   already does this).
5. **Marker highlight**: a clay highlighter stroke draws under a headline's key word.
6. **Floating phone tab dock** with a clay dot on the active tab (changes the phone layout).
7. **Logo halo**: a pulsing ring round the logo on the empty chat.

All would stop under `prefers-reduced-motion`.

## Motion and controls kit (2026-11-06)

The owner asked for "trendy new innovative controls and animations wherever possible". Orbit layout
and alignment are unchanged; only behaviour and finish were added, in navy and brass.

- `frontend/src/lib/fx.ts` (`installFx()` in `main.tsx`): pointer spotlight on cards (`--mx/--my`),
  3D tilt on `[data-tilt]`, ripple on pill buttons. Skipped when the OS asks for reduced motion.
- `frontend/src/index.css` `fx-*` classes: aurora backdrop, primary-button glow and sweep, press scale,
  card spotlight + brass border on hover, input focus halo, `fx-stagger` rise-in lists, `fx-beam`
  conic border on the chat composer, `fx-skeleton` shimmer, `fx-gradient-text`, `fx-ping`.
- Sliding `layoutId` pills: sign-in role toggle, lawyer filters, phone tab bar indicator.
- Route transitions (fade, rise, de-blur) in `AppShell`; staggered answer paragraphs and trace steps
  in chat; `CountUp` numbers on the dashboard and lawyer portal; skeleton rows in `LoadingState`.
- `MotionConfig reducedMotion="user"` plus a `prefers-reduced-motion` CSS override turn it all off.
- Screens: `/mnt/project-files/nya-ai/motion-kit/`.

## Orbit Dial menu + Statute Timeline (2026-11-06)

The owner found the menu, chat history and dashboard "very common" and picked, from three concepts
(https://claude.ai/artifact/4XtQvvZRr8SrAgxN19uRyJ), the mix of the Orbit Dial menu and the Statute
Timeline. This replaces the Orbit sidebar and phone tab bar; other Orbit layouts stay.

- **Menu** (`components/OrbMenu.tsx`): the logo is an orb in a slim top bar. Tapping it dims the page
  and fans the sections out along one orbit (Ask, My matters, Advocates, Consultations, Account; for
  advocates Dashboard, Messages, Profile), with Plus and the info links under it. Esc or a tap outside
  closes it. The bar shows the current section as "§ NAME".
- **History** (`components/MattersTimeline.tsx`, `/dashboard`): questions placed by incident date on
  a line split at 1 July 2024 (IPC/CrPC side, BNS/BNSS/BSA side). Undated questions are chips; the
  selected one opens its conversation (`/chat?c=<id>`).
- **Dashboard**: three figures, the timeline, "Clocks running" (limitation periods from
  `backend/app/services/deadlines.py`, counted from the incident date) and the next consultation.
- **Chat**: a "When did it happen?" date chip under the composer sends `incident_date`, which sets
  the law in force for the agent and starts the clocks.
- Screens: `/mnt/project-files/nya-ai/orbit-dial-timeline/`.

## Not done yet

- No dark mode. The tokens are plain hex, so a dark mode would first move them to CSS variables.
- The Orbit canvas artifact still shows the old navy theme; the app is now the reference for colour.
