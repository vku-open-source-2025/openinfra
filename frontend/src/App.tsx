import React, { useEffect } from 'react';
import { BrowserRouter, Routes, Route, Navigate, useNavigate } from 'react-router-dom';
import Dashboard from './pages/Dashboard';
import HomePage from './pages/HomePage';
import PublicMap from './pages/PublicMap';
import AdminLogin from './pages/AdminLogin';
import ApiDocsPage from './pages/ApiDocsPage';

const RequireAuth = ({ children }: { children: React.ReactElement }) => {
  const navigate = useNavigate();

  useEffect(() => {
    const token = localStorage.getItem('access-token');
    if (!token) {
      navigate('/admin/login', { replace: true });
    }
  }, [navigate]);

  const token = typeof window !== 'undefined' ? localStorage.getItem('access-token') : null;
  if (!token) {
    return (
      <div className="flex h-screen items-center justify-center bg-slate-50">
        <div className="text-center text-slate-500 font-medium">Đang kiểm tra phiên đăng nhập...</div>
      </div>
    );
  }

  return children;
};

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/map" element={<PublicMap />} />
        <Route path="/docs" element={<ApiDocsPage />} />
        <Route path="/admin/login" element={<AdminLogin />} />
        <Route
          path="/admin"
          element={
            <RequireAuth>
              <Dashboard />
            </RequireAuth>
          }
        />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
