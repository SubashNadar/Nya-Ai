export type Role = 'user' | 'lawyer'

export interface User {
  id: string
  role: Role
  name: string
  initials: string
  phone: string | null
}

/** How an AI reply was made: "agent" (R1 graph) or "basic" (rule-engine fallback). */
export interface ChatMeta {
  mode: 'agent' | 'basic'
  status:
    | 'answered'
    | 'pending_review'
    | 'reviewed'
    | 'rejected'
    | 'emergency'
    | 'refused'
    | 'no_evidence'
    | null
  escalation: 'none' | 'offer_lawyer' | 'advocate_review' | 'emergency' | 'refused' | null
  risk: string | null
  route: 'none' | 'rag' | 'sql' | 'hybrid' | null
  confidence: number | null
  confidence_label: 'High' | 'Medium' | 'Low' | null
  trace: string[]
  trace_id: string | null
  review_id: string | null
}

export interface ChatMessage {
  id: string
  role: 'user' | 'ai'
  text: string
  points: string[]
  citation: string
  cta: boolean
  meta?: ChatMeta | null
  created_at: string
}

export type ReviewDecision = 'approved' | 'edited' | 'rejected'

/** An answer the agent holds for a verified advocate (lawyer portal review queue). */
export interface AnswerReview {
  id: string
  thread_id: string
  conversation_id: string | null
  question: string
  draft: {
    text: string
    points: string[]
    citations: { act: string; section: string; heading: string }[]
    model: string
  } | null
  critique: { verdict: string; confidence: number; confidence_label: string } | null
  status: 'pending' | ReviewDecision
  decided_by: string | null
  final: Record<string, unknown> | null
  trace_id: string | null
  created_at: string
  decided_at: string | null
}

export interface ReviewDecisionIn {
  decision: ReviewDecision
  text?: string
  points?: string[]
  note?: string
}

export interface LawyerCard {
  id: string
  name: string
  initials: string
  avatar_color: string
  spec: string
  category: string
  exp: number
  langs: string[]
  rating: number
  reviews: number
  next_slot: string
}

export interface LawyerDetail extends LawyerCard {
  bio: string
  bar_council_id: string
  price: number
  price_struck: number
}

export type ConsultType = 'Video' | 'Phone'

export type BookingStatus =
  | 'pending_payment'
  | 'paid'
  | 'accepted'
  | 'declined'
  | 'completed'

export interface ConsultBrief {
  topic: string
  facts: string
  questions: string[]
  goals: string[]
}

export interface Booking {
  id: string
  ref: string
  lawyer: LawyerCard
  user_id: string
  client_name: string | null
  client_initials: string | null
  topic: string | null
  brief: ConsultBrief | null
  day_label: string
  slot_label: string
  consult_type: ConsultType
  fee: number
  lawyer_share: number
  status: BookingStatus
  created_at: string
}

export type PaymentMethod = 'upi' | 'card' | 'netbanking'

export interface PaymentOrder {
  order_id: string
  razorpay_order_id: string
  razorpay_key_id: string
  amount: number
  currency: string
  status: 'created'
  prefill: { name: string | null; contact: string | null; email: string | null }
}

export interface RazorpayResult {
  razorpay_payment_id: string
  razorpay_order_id: string
  razorpay_signature: string
}

export interface UserDashboard {
  questions_answered: number
  consults_booked: number
  saved_amount: number
  upcoming: Booking | null
  recent_questions: { q: string; when: string }[]
}

export interface LawyerDashboard {
  earnings_month: number
  consultations: number
  rating: number
  reviews: number
  share_pct: number
  requests: Booking[]
}

export interface Message {
  id: string
  sender: 'client' | 'lawyer'
  text: string
  created_at: string
}

export interface MessageThread {
  id: string
  client_name: string
  client_initials: string
  topic: string
  unread: boolean
  messages: Message[]
}

export interface ApiErrorShape {
  detail?: string | Record<string, unknown>
}

export type SupportTopic = 'booking' | 'answer' | 'privacy' | 'advocate' | 'other'

export interface SupportIn {
  name: string
  contact: string
  topic: SupportTopic
  text: string
}

export interface SupportOut {
  ref: string
  created_at: string
}

// ---- Answer feedback, consult planner, law library admin ----

export interface FeedbackIn {
  message_id: string
  rating: 'up' | 'down'
  reason?: 'wrong' | 'unclear' | 'unsafe' | 'other'
  comment?: string
}

export interface FeedbackOut {
  id: string
  message_id: string
  rating: 'up' | 'down'
  reason: string | null
  created_at: string
}

export interface PlanDraft {
  brief: ConsultBrief
  documents: string[]
  source: 'rules' | 'model'
}

export interface IngestionJob {
  id: number
  act: string
  stage: string
  status: 'running' | 'ok' | 'failed'
  stats: Record<string, unknown>
  started_at: string
  finished_at: string | null
}

export interface LibraryAct {
  code: string
  title: string
  in_force_from: string
  repealed_on: string | null
  replaced_by: string | null
  sections: number
  ingested_at: string | null
  pdf_present: boolean
  last_job: IngestionJob | null
}

export interface LibraryOverview {
  reachable: boolean
  azure: boolean
  acts: LibraryAct[]
  jobs: IngestionJob[]
}

// ---- Matters (GET /api/chat/matters) ----

export type MatterStatus = 'answered' | 'advocate_review' | 'reviewed' | 'lawyer_suggested' | 'emergency' | 'refused'

export interface Matter {
  conversation_id: string
  question_id: string
  question: string
  asked_at: string
  incident_date: string | null
  /** "old" = IPC/CrPC era (before 1 July 2024), "new" = BNS/BNSS/BSA. */
  code: 'old' | 'new' | null
  citation: string
  status: MatterStatus
}

export interface DeadlineClock {
  conversation_id: string
  question: string
  title: string
  rule: string
  starts: string | null
  due: string | null
  days_left: number | null
}

export interface MattersResponse {
  matters: Matter[]
  clocks: DeadlineClock[]
}
