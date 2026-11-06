import type { ReactNode } from 'react'
import { Navigate, Route, Routes } from 'react-router-dom'
import { AppShell } from './components/AppShell'
import { InfoLayout } from './components/InfoLayout'
import { useAuth } from './context/AuthContext'
import LoginPage from './pages/LoginPage'
import ChatPage from './pages/ChatPage'
import LawyersPage from './pages/LawyersPage'
import BookingPage from './pages/BookingPage'
import PaymentPage from './pages/PaymentPage'
import SuccessPage from './pages/SuccessPage'
import DashboardPage from './pages/DashboardPage'
import BookingsPage from './pages/BookingsPage'
import AccountPage from './pages/AccountPage'
import LawyerPortalPage from './pages/LawyerPortalPage'
import LawyerMessagesPage from './pages/LawyerMessagesPage'
import LawyerProfilePage from './pages/LawyerProfilePage'
import LegalPage from './pages/LegalPage'
import AboutPage from './pages/AboutPage'
import ContactPage from './pages/ContactPage'
import HelpPage from './pages/HelpPage'
import ConsultPlanPage from './pages/ConsultPlanPage'
import CallPage from './pages/CallPage'
import LibraryPage from './pages/LibraryPage'

function homeFor(role: 'user' | 'lawyer' | undefined) {
  return role === 'lawyer' ? '/portal' : '/chat'
}

function RequireAuth({ children }: { children: ReactNode }) {
  const { user, loading } = useAuth()
  if (loading) return null
  if (!user) return <Navigate to="/login" replace />
  return <>{children}</>
}

function RequireRole({ role, children }: { role: 'user' | 'lawyer'; children: ReactNode }) {
  const { user, loading } = useAuth()
  if (loading) return null
  if (!user) return <Navigate to="/login" replace />
  if (user.role !== role) return <Navigate to={homeFor(user.role)} replace />
  return <>{children}</>
}

function RedirectIfAuthed({ children }: { children: ReactNode }) {
  const { user, loading } = useAuth()
  if (loading) return null
  if (user) return <Navigate to={homeFor(user.role)} replace />
  return <>{children}</>
}

export default function App() {
  const { loading } = useAuth()

  if (loading) {
    return <div className="flex min-h-[100dvh] items-center justify-center bg-bg text-sm text-muted">Loading…</div>
  }

  return (
    <Routes>
      <Route
        path="/login"
        element={
          <RedirectIfAuthed>
            <LoginPage />
          </RedirectIfAuthed>
        }
      />

      <Route element={<InfoLayout />}>
        <Route path="/legal" element={<LegalPage />} />
        <Route path="/about" element={<AboutPage />} />
        <Route path="/contact" element={<ContactPage />} />
        <Route path="/help" element={<HelpPage />} />
      </Route>

      <Route
        element={
          <RequireAuth>
            <AppShell />
          </RequireAuth>
        }
      >
        <Route
          path="/chat"
          element={
            <RequireRole role="user">
              <ChatPage />
            </RequireRole>
          }
        />
        <Route
          path="/lawyers"
          element={
            <RequireRole role="user">
              <LawyersPage />
            </RequireRole>
          }
        />
        <Route
          path="/plan"
          element={
            <RequireRole role="user">
              <ConsultPlanPage />
            </RequireRole>
          }
        />
        <Route path="/call/:bookingId" element={<CallPage />} />
        <Route
          path="/booking/:lawyerId"
          element={
            <RequireRole role="user">
              <BookingPage />
            </RequireRole>
          }
        />
        <Route
          path="/pay/:bookingId"
          element={
            <RequireRole role="user">
              <PaymentPage />
            </RequireRole>
          }
        />
        <Route
          path="/success/:bookingId"
          element={
            <RequireRole role="user">
              <SuccessPage />
            </RequireRole>
          }
        />
        <Route
          path="/dashboard"
          element={
            <RequireRole role="user">
              <DashboardPage />
            </RequireRole>
          }
        />
        <Route
          path="/bookings"
          element={
            <RequireRole role="user">
              <BookingsPage />
            </RequireRole>
          }
        />
        <Route
          path="/account"
          element={
            <RequireRole role="user">
              <AccountPage />
            </RequireRole>
          }
        />

        <Route
          path="/portal"
          element={
            <RequireRole role="lawyer">
              <LawyerPortalPage />
            </RequireRole>
          }
        />
        <Route
          path="/messages"
          element={
            <RequireRole role="lawyer">
              <LawyerMessagesPage />
            </RequireRole>
          }
        />
        <Route
          path="/profile"
          element={
            <RequireRole role="lawyer">
              <LawyerProfilePage />
            </RequireRole>
          }
        />
        <Route
          path="/library"
          element={
            <RequireRole role="lawyer">
              <LibraryPage />
            </RequireRole>
          }
        />
      </Route>

      <Route path="/" element={<Navigate to="/login" replace />} />
      <Route path="*" element={<Navigate to="/login" replace />} />
    </Routes>
  )
}
