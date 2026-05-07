import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import Login from "./pages/Login";
import Dashboard from "./pages/Dashboard";
import CameraConfig from "./pages/CameraConfig";
import AlertHistory from "./pages/AlertHistory";
import UserManagement from "./pages/UserManagement";
import Navbar from "./components/Navbar";

function PrivateRoute({ children }) {
  return localStorage.getItem("token") ? children : <Navigate to="/login" />;
}

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/*" element={
          <PrivateRoute>
            <div className="app-shell">
              <Navbar />
              <div className="page-content">
                <Routes>
                  <Route path="/" element={<Dashboard />} />
                  <Route path="/config" element={<CameraConfig />} />
                  <Route path="/alerts" element={<AlertHistory />} />
                  <Route path="/users" element={<UserManagement />} />
                </Routes>
              </div>
            </div>
          </PrivateRoute>
        } />
      </Routes>
    </BrowserRouter>
  );
}