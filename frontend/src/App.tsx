import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import Dashboard from './pages/Dashboard'
import Landing from './pages/Landing'
import Results from './pages/Results'
import StrategyTesting from './pages/StrategyTesting'
import LiveTradingPage from './pages/LiveTradingPage'
import About from './pages/About'
import Tutorial from './pages/Tutorial'
import Login from './pages/Login'
import Tickets from './pages/Tickets'
import CompleteProfile from './pages/CompleteProfile'
import Profile from './pages/Profile'
import Navbar from './components/Navbar'
import ProtectedRoute from './components/ProtectedRoute'
import NavigationSetup from './components/NavigationSetup'
import { SymbolProvider } from './context/SymbolContext'
import { ToastProvider } from './components/ToastProvider'
import { AuthProvider, useAuth } from './context/AuthContext'

// Component to conditionally show Landing or Dashboard
function Home() {
  const { isAuthenticated, isLoading } = useAuth()
  
  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-900 flex items-center justify-center">
        <div className="text-center">
          <div className="inline-block animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500 mb-4"></div>
          <div className="text-white text-xl">در حال بارگذاری...</div>
        </div>
      </div>
    )
  }
  
  return isAuthenticated ? <Dashboard /> : <Landing />
}

function App() {
  return (
    <Router>
      <NavigationSetup />
      <AuthProvider>
        <ToastProvider>
          <SymbolProvider>
            <div className="min-h-screen bg-gray-900">
              <Navbar />
              <Routes>
                <Route path="/login" element={<Login />} />
                <Route
                  path="/complete-profile"
                  element={
                    <ProtectedRoute>
                      <CompleteProfile />
                    </ProtectedRoute>
                  }
                />
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
                  path="/tickets"
                  element={
                    <ProtectedRoute>
                      <Tickets />
                    </ProtectedRoute>
                  }
                />
                <Route path="/about" element={<About />} />
                <Route path="/tutorial" element={<Tutorial />} />
              </Routes>
            </div>
          </SymbolProvider>
        </ToastProvider>
      </AuthProvider>
    </Router>
  )
}

export default App

