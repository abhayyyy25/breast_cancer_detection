import React from "react";
import { Routes, Route, Navigate } from "react-router-dom";
import "./styles/enterpriseDesignSystem.css";
import "./App.css";
import Login from "./components/Login";
import Signup from "./components/Signup";
import ProtectedRoute from "./components/ProtectedRoute";
import RoleBasedDashboard from "./components/RoleBasedDashboard";
import PatientDetails from "./components/PatientDetails";
import OrganizationDetails from "./components/OrganizationDetails";

function App() {
  return (
    <Routes>
      {/* Public Routes */}
      <Route path="/login" element={<Login />} />
      <Route path="/signup" element={<Signup />} />
      
      {/* Protected Routes - Role-Based Dashboards */}
      <Route
        path="/superadmin"
        element={
          <ProtectedRoute>
            <RoleBasedDashboard />
          </ProtectedRoute>
        }
      />
      <Route
        path="/superadmin/*"
        element={
          <ProtectedRoute>
            <RoleBasedDashboard />
          </ProtectedRoute>
        }
      />
      <Route
        path="/admin"
        element={
          <ProtectedRoute>
            <RoleBasedDashboard />
          </ProtectedRoute>
        }
      />
      <Route
        path="/admin/*"
        element={
          <ProtectedRoute>
            <RoleBasedDashboard />
          </ProtectedRoute>
        }
      />
      <Route
        path="/doctor"
        element={
          <ProtectedRoute>
            <RoleBasedDashboard />
          </ProtectedRoute>
        }
      />
      <Route
        path="/doctor/*"
        element={
          <ProtectedRoute>
            <RoleBasedDashboard />
          </ProtectedRoute>
        }
      />
      <Route
        path="/patient"
        element={
          <ProtectedRoute>
            <RoleBasedDashboard />
          </ProtectedRoute>
        }
      />
      <Route
        path="/patient/*"
        element={
          <ProtectedRoute>
            <RoleBasedDashboard />
          </ProtectedRoute>
        }
      />
      
      {/* Protected Routes - Detail Pages */}
      <Route
        path="/admin/patient/:id"
        element={
          <ProtectedRoute>
            <PatientDetails />
          </ProtectedRoute>
        }
      />
      <Route
        path="/doctor/patient/:id"
        element={
          <ProtectedRoute>
            <PatientDetails />
          </ProtectedRoute>
        }
      />
      <Route
        path="/superadmin/organization/:id"
        element={
          <ProtectedRoute>
            <OrganizationDetails />
          </ProtectedRoute>
        }
      />
      
      {/* Root Dashboard Route */}
      <Route
        path="/"
        element={
          <ProtectedRoute>
            <RoleBasedDashboard />
          </ProtectedRoute>
        }
      />
      <Route
        path="/dashboard"
        element={
          <ProtectedRoute>
            <RoleBasedDashboard />
          </ProtectedRoute>
        }
      />
      
      {/* Redirect to login if no match */}
      <Route path="*" element={<Navigate to="/login" replace />} />
    </Routes>
  );
}

export default App;
