import axios, { type AxiosInstance } from 'axios'
import type {
  AnswerReview,
  Booking,
  ChatMessage,
  ChatMeta,
  ConsultBrief,
  ConsultType,
  FeedbackIn,
  FeedbackOut,
  LibraryOverview,
  PlanDraft,
  ReviewDecisionIn,
  LawyerDashboard,
  LawyerCard,
  LawyerDetail,
  MessageThread,
  PaymentMethod,
  PaymentOrder,
  RazorpayResult,
  Role,
  SupportIn,
  SupportOut,
  User,
  UserDashboard,
} from '../types'

const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000/api'

const TOKEN_STORAGE_KEY = 'nya_ai_token'

export function getStoredToken(): string | null {
  return localStorage.getItem(TOKEN_STORAGE_KEY)
}

export function setStoredToken(token: string | null) {
  if (token) {
    localStorage.setItem(TOKEN_STORAGE_KEY, token)
  } else {
    localStorage.removeItem(TOKEN_STORAGE_KEY)
  }
}

const client: AxiosInstance = axios.create({ baseURL: BASE_URL })

client.interceptors.request.use((config) => {
  const token = getStoredToken()
  if (token) {
    config.headers = config.headers ?? {}
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

export function getApiErrorMessage(err: unknown): string {
  if (axios.isAxiosError(err)) {
    const detail = err.response?.data?.detail
    if (typeof detail === 'string') return detail
    if (detail && typeof detail === 'object') return JSON.stringify(detail)
    if (err.message) return err.message
  }
  if (err instanceof Error) return err.message
  return 'Something went wrong. Please try again.'
}

// ---- Auth ----

export async function requestOtp(phone: string): Promise<{ sent: true }> {
  const { data } = await client.post('/auth/otp/request', { phone })
  return data
}

export async function verifyOtp(
  phone: string,
  otp: string,
  role?: Role,
): Promise<{ token: string; user: User }> {
  const { data } = await client.post('/auth/otp/verify', { phone, otp, role })
  return data
}

export async function guestLogin(role: 'user' | 'lawyer'): Promise<{ token: string; user: User }> {
  const { data } = await client.post('/auth/guest', { role })
  return data
}

export async function getMe(): Promise<{ user: User }> {
  const { data } = await client.get('/auth/me')
  return data
}

export async function logout(): Promise<void> {
  await client.post('/auth/logout')
}

// ---- Chat ----

export async function sendChatMessage(
  message: string,
  conversationId?: string,
): Promise<{
  conversation_id: string
  id: string
  text: string
  points: string[]
  citation: string
  cta: boolean
  meta?: ChatMeta | null
}> {
  const { data } = await client.post('/chat/message', {
    message,
    conversation_id: conversationId,
  })
  return data
}

export async function getChatHistory(
  conversationId?: string,
): Promise<{ messages: ChatMessage[] }> {
  const { data } = await client.get('/chat/history', {
    params: conversationId ? { conversation_id: conversationId } : {},
  })
  return data
}

// ---- Lawyers ----

export async function getLawyers(category?: string): Promise<{ lawyers: LawyerCard[] }> {
  const { data } = await client.get('/lawyers', {
    params: category && category !== 'All' ? { category } : {},
  })
  return data
}

export async function getLawyer(id: string): Promise<LawyerDetail> {
  const { data } = await client.get(`/lawyers/${id}`)
  return data
}

// ---- Bookings ----

export async function createBooking(payload: {
  lawyer_id: string
  day_label: string
  slot_label: string
  consult_type: ConsultType
  brief?: ConsultBrief | null
}): Promise<Booking> {
  const { data } = await client.post('/bookings', payload)
  return data
}

export async function getMyBookings(): Promise<{ bookings: Booking[] }> {
  const { data } = await client.get('/bookings/me')
  return data
}

export async function getBooking(id: string): Promise<Booking> {
  const { data } = await client.get(`/bookings/${id}`)
  return data
}

export async function respondToBooking(
  id: string,
  action: 'accept' | 'decline',
): Promise<Booking> {
  const { data } = await client.patch(`/bookings/${id}/respond`, { action })
  return data
}

// ---- Payments ----

export async function createPaymentOrder(
  bookingId: string,
  method: PaymentMethod,
): Promise<PaymentOrder> {
  const { data } = await client.post('/payments/order', {
    booking_id: bookingId,
    method,
  })
  return data
}

export async function confirmPayment(
  orderId: string,
  result: RazorpayResult,
): Promise<{ status: 'paid'; booking: Booking }> {
  const { data } = await client.post(`/payments/${orderId}/confirm`, result)
  return data
}

let razorpayScriptPromise: Promise<void> | null = null

export function loadRazorpayScript(): Promise<void> {
  if (window.Razorpay) return Promise.resolve()
  if (razorpayScriptPromise) return razorpayScriptPromise
  razorpayScriptPromise = new Promise((resolve, reject) => {
    const script = document.createElement('script')
    script.src = 'https://checkout.razorpay.com/v1/checkout.js'
    script.onload = () => resolve()
    script.onerror = () => reject(new Error('Failed to load payment gateway script'))
    document.body.appendChild(script)
  })
  return razorpayScriptPromise
}

// ---- Dashboard ----

export async function getUserDashboard(): Promise<UserDashboard> {
  const { data } = await client.get('/dashboard/user')
  return data
}

export async function getLawyerDashboard(): Promise<LawyerDashboard> {
  const { data } = await client.get('/dashboard/lawyer')
  return data
}

// ---- Messages (lawyer inbox — see docs/DECISIONS.md) ----

export async function getMessageThreads(): Promise<{ threads: MessageThread[] }> {
  const { data } = await client.get('/messages/threads')
  return data
}

export async function getMessageThread(id: string): Promise<MessageThread> {
  const { data } = await client.get(`/messages/threads/${id}`)
  return data
}

export async function replyToThread(
  id: string,
  text: string,
): Promise<{ message: MessageThread['messages'][number] }> {
  const { data } = await client.post(`/messages/threads/${id}/reply`, { text })
  return data
}

export async function markThreadRead(id: string): Promise<MessageThread> {
  const { data } = await client.patch(`/messages/threads/${id}/read`)
  return data
}

export async function sendAnswerFeedback(payload: FeedbackIn): Promise<FeedbackOut> {
  const { data } = await client.post('/chat/feedback', payload)
  return data
}

// ---------- Consult planner ----------

export async function draftConsultPlan(payload: {
  conversation_id?: string
  question?: string
}): Promise<PlanDraft> {
  const { data } = await client.post('/plan/draft', payload)
  return data
}

// ---------- Law library admin (advocate accounts) ----------

export async function getLibrary(): Promise<LibraryOverview> {
  const { data } = await client.get('/library/acts')
  return data
}

export async function startIngestion(acts: string[]): Promise<{ started: string[] }> {
  const { data } = await client.post('/library/ingest', { acts })
  return data
}

// ---------- Advocate review queue (lawyer portal) ----------

export async function getReviews(
  status: 'pending' | 'approved' | 'edited' | 'rejected' = 'pending',
): Promise<{ reviews: AnswerReview[] }> {
  const { data } = await client.get('/reviews', { params: { status } })
  return data
}

export async function getReview(id: string): Promise<AnswerReview> {
  const { data } = await client.get(`/reviews/${id}`)
  return data
}

export async function decideReview(id: string, payload: ReviewDecisionIn): Promise<AnswerReview> {
  const { data } = await client.post(`/reviews/${id}`, payload)
  return data
}

// ---------- Support ----------

export async function sendSupportMessage(payload: SupportIn): Promise<SupportOut> {
  const { data } = await client.post('/support', payload)
  return data
}

export default client
