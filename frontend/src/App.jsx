import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import Navbar from './components/Navbar';

// Pages
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import CaseList from './pages/CaseList';
import CreateCase from './pages/CreateCase';
import CaseOverview from './pages/CaseOverview';
import Statements from './pages/Statements';
import Accounts from './pages/Accounts';
import Transactions from './pages/Transactions';
import Detectors from './pages/Detectors';
import Suspicious from './pages/Suspicious';
import FundFlow from './pages/FundFlow';
import CircularFlows from './pages/CircularFlows';
import Layering from './pages/Layering';
import MoneyTrail from './pages/MoneyTrail';
import AiInvestigation from './pages/AiInvestigation';
import Reports from './pages/Reports';
import History from './pages/History';

function ProtectedRoute({ children }) {
  const { user, loading } = useAuth();
  if (loading) {
    return <div className="min-h-screen bg-slate-950 flex items-center justify-center text-slate-400">Loading FINTELLIGENCE...</div>;
  }
  if (!user) {
    return <Navigate to="/login" replace />;
  }
  return children;
}

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans">
          <Navbar />
          <main className="flex-1">
            <Routes>
              {/* Public route */}
              <Route path="/login" element={<Login />} />

              {/* Protected routes */}
              <Route path="/dashboard" element={<ProtectedRoute><Dashboard /></ProtectedRoute>} />
              <Route path="/cases" element={<ProtectedRoute><CaseList /></ProtectedRoute>} />
              <Route path="/cases/new" element={<ProtectedRoute><CreateCase /></ProtectedRoute>} />

              {/* Case nested module routes */}
              <Route path="/cases/:id" element={<ProtectedRoute><CaseOverview /></ProtectedRoute>} />
              <Route path="/cases/:id/statements" element={<ProtectedRoute><Statements /></ProtectedRoute>} />
              <Route path="/cases/:id/accounts" element={<ProtectedRoute><Accounts /></ProtectedRoute>} />
              <Route path="/cases/:id/transactions" element={<ProtectedRoute><Transactions /></ProtectedRoute>} />
              <Route path="/cases/:id/detectors" element={<ProtectedRoute><Detectors /></ProtectedRoute>} />
              <Route path="/cases/:id/suspicious" element={<ProtectedRoute><Suspicious /></ProtectedRoute>} />
              <Route path="/cases/:id/fund-flow" element={<ProtectedRoute><FundFlow /></ProtectedRoute>} />
              <Route path="/cases/:id/circular-flows" element={<ProtectedRoute><CircularFlows /></ProtectedRoute>} />
              <Route path="/cases/:id/layering" element={<ProtectedRoute><Layering /></ProtectedRoute>} />
              <Route path="/cases/:id/money-trail" element={<ProtectedRoute><MoneyTrail /></ProtectedRoute>} />
              <Route path="/cases/:id/investigation" element={<ProtectedRoute><AiInvestigation /></ProtectedRoute>} />
              <Route path="/cases/:id/reports" element={<ProtectedRoute><Reports /></ProtectedRoute>} />
              <Route path="/cases/:id/history" element={<ProtectedRoute><History /></ProtectedRoute>} />

              {/* Catch-all */}
              <Route path="*" element={<Navigate to="/dashboard" replace />} />
            </Routes>
          </main>
        </div>
      </BrowserRouter>
    </AuthProvider>
  );
}
