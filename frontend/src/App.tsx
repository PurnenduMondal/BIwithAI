import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Toaster } from 'react-hot-toast';
import { ErrorBoundary } from './components/common/ErrorBoundary';
import { MainLayout } from './components/layout/MainLayout';
import { ProtectedRoute } from './components/auth/ProtectedRoute';
import { LoginForm } from './components/auth/LoginForm';
import { RegisterForm } from './components/auth/RegisterForm';
import { Home } from './pages/Home';
import { DashboardList } from './pages/DashboardList';
import { DashboardView } from './pages/DashboardView';
import { DashboardCreate } from './pages/DashboardCreate';
import { DataSourceList } from './pages/DataSourceList';
import { DataSourceCreate } from './pages/DataSourceCreate';
import { DataSourceView } from './pages/DataSourceView';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
      staleTime: 5 * 60 * 1000, // 5 minutes
    },
  },
});

function App() {
  return (
    <ErrorBoundary>
      <QueryClientProvider client={queryClient}>
        <BrowserRouter>
        <Routes>         
          {/* Public Routes */}
          <Route path="/login" element={<LoginForm />} />
          <Route path="/register" element={<RegisterForm />} />

          {/* Protected Routes */}
          <Route element={<ProtectedRoute />}>
            <Route element={<MainLayout />}>
              <Route path="/" element={<Home />} />
              
              {/* Dashboards */}
              <Route path="/dashboards" element={<DashboardList />} />
              <Route path="/dashboards/create" element={<DashboardCreate />} />
              <Route path="/dashboards/:id" element={<DashboardView />} />
              
              {/* Data Sources */}
              <Route path="/data-sources" element={<DataSourceList />} />
              <Route path="/data-sources/create" element={<DataSourceCreate />} />
              <Route path="/data-sources/:id" element={<DataSourceView />} />
              
              {/* Other Routes */}
              <Route path="/test" element={<div className="p-6"><h1 className="text-2xl font-bold text-green-600">Test Route Working!</h1><p className="mt-4">If you can see this, the layout and routing are working correctly.</p></div>} />
              <Route path="/alerts" element={<div className="p-6"><h1 className="text-2xl font-bold">Alerts (Coming Soon)</h1></div>} />
              <Route path="/settings" element={<div className="p-6"><h1 className="text-2xl font-bold">Settings (Coming Soon)</h1></div>} />
            </Route>
          </Route>

          {/* 404 */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
        </BrowserRouter>

        <Toaster
          position="top-right"
          toastOptions={{
            duration: 3000,
            style: {
              background: '#fff',
              color: '#333',
              boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)',
            },
          }}
        />
      </QueryClientProvider>
    </ErrorBoundary>
  );
}

export default App;