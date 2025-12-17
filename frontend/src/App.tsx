import React from 'react'
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import Dashboard from './pages/Dashboard'
import Landing from './pages/Landing'
import Results from './pages/Results'
import StrategyTesting from './pages/StrategyTesting'
import StrategyMarketplace from './pages/StrategyMarketplace'
import LiveTradingPage from './pages/LiveTradingPage'
import About from './pages/About'
import Tutorial from './pages/Tutorial'
import Terms from './pages/Terms'
import Login from './pages/Login'
import Tickets from './pages/Tickets'
import Profile from './pages/Profile'
import AdminSecurity from './pages/AdminSecurity'
import AdminUserManagement from './pages/AdminUserManagement'
import AdminAnalytics from './pages/AdminAnalytics'
import SystemSettings from './pages/SystemSettings'
import FreeGoldAPIGuide from './pages/FreeGoldAPIGuide'
import NotFound from './pages/NotFound'
import Blog from './pages/Blog'
import BlogPost from './pages/BlogPost'
import Navbar from './components/Navbar'
import Footer from './components/Footer'
import ProtectedRoute from './components/ProtectedRoute'
import NavigationSetup from './components/NavigationSetup'
import { SymbolProvider } from './context/SymbolContext'
import { ToastProvider } from './components/ToastProvider'
import { AuthProvider, useAuth } from './context/AuthContext'
import { FeatureFlagsProvider } from './context/FeatureFlagsContext'
import { ProfileCompletionProvider } from './context/ProfileCompletionContext'
import GoogleAnalytics from './components/GoogleAnalytics'
import { setupPageTracking } from './utils/analytics'

// Component to conditionally show Landing or Dashboard
function Home() {
  const { isAuthenticated, isLoading } = useAuth()
  const [showLoading, setShowLoading] = React.useState(true)
  
  // Show loading spinner only for a short time (max 2 seconds)
  // After that, show Landing if not authenticated, or Dashboard if authenticated
  React.useEffect(() => {
    if (!isLoading) {
      setShowLoading(false)
    } else {
      // Set a timeout to stop showing loading after 2 seconds
      const timer = setTimeout(() => {
        setShowLoading(false)
      }, 2000)
      return () => clearTimeout(timer)
    }
  }, [isLoading])
  
  // If authenticated, show Dashboard (even if still loading)
  if (isAuthenticated) {
    return <Dashboard />
  }
  
  // If still loading and we should show loading spinner, show it
  if (isLoading && showLoading) {
    return (
      <div className="min-h-screen bg-gray-900 flex items-center justify-center">
        <div className="text-center">
          <div className="inline-block animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500 mb-4"></div>
          <div className="text-white text-xl">در حال بارگذاری...</div>
        </div>
      </div>
    )
  }
  
  // Show Landing page (default for unauthenticated users)
  return <Landing />
}

function App() {
  // Setup analytics tracking
  React.useEffect(() => {
    setupPageTracking()
  }, [])

  return (
    <Router>
      <GoogleAnalytics />
      <NavigationSetup />
      <AuthProvider>
        <ProfileCompletionProvider>
          <FeatureFlagsProvider>
            <ToastProvider>
              <SymbolProvider>
                <div className="min-h-screen bg-gray-900 flex flex-col">
                  <Navbar />
                  <main className="flex-grow">
                    <Routes>
                    <Route path="/login" element={<Login />} />
                    <Route path="/complete-profile" element={<Navigate to="/profile" replace />} />
                    <Route
                      path="/profile"
                      element={
                        <ProtectedRoute>
                          <Profile />
                        </ProtectedRoute>
                      }
                    />
                    <Route path="/" element={<Home />} />
                    <Route
                      path="/results"
                      element={
                        <ProtectedRoute>
                          <Results />
                        </ProtectedRoute>
                      }
                    />
                    <Route
                      path="/testing"
                      element={
                        <ProtectedRoute>
                          <StrategyTesting />
                        </ProtectedRoute>
                      }
                    />
                    <Route
                      path="/trading"
                      element={
                        <ProtectedRoute>
                          <LiveTradingPage />
                        </ProtectedRoute>
                      }
                    />
                    <Route
                      path="/marketplace"
                      element={
                        <ProtectedRoute>
                          <StrategyMarketplace />
                        </ProtectedRoute>
                      }
                    />
                    <Route
                      path="/tickets"
                      element={
                        <ProtectedRoute>
                          <Tickets />
                        </ProtectedRoute>
                      }
                    />
                    <Route
                      path="/admin/security"
                      element={
                        <ProtectedRoute>
                          <AdminSecurity />
                        </ProtectedRoute>
                      }
                    />
                    <Route
                      path="/admin/users"
                      element={
                        <ProtectedRoute>
                          <AdminUserManagement />
                        </ProtectedRoute>
                      }
                    />
                    <Route
                      path="/admin/analytics"
                      element={
                        <ProtectedRoute>
                          <AdminAnalytics />
                        </ProtectedRoute>
                      }
                    />
                    <Route
                      path="/admin/settings"
                      element={
                        <ProtectedRoute>
                          <SystemSettings />
                        </ProtectedRoute>
                      }
                    />
                    <Route path="/about" element={<About />} />
                    <Route path="/tutorial" element={<Tutorial />} />
                    <Route path="/terms" element={<Terms />} />
                    <Route path="/blog" element={<Blog />} />
                    <Route path="/blog/:slug" element={<BlogPost />} />
                    <Route path="/guides/free-gold-api" element={<FreeGoldAPIGuide />} />
                    <Route path="*" element={<NotFound />} />
                    </Routes>
                  </main>
                  <Footer />
                </div>
              </SymbolProvider>
            </ToastProvider>
          </FeatureFlagsProvider>
        </ProfileCompletionProvider>
      </AuthProvider>
    </Router>
  )
}

export default App

