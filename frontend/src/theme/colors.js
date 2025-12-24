/**
 * Medical Color Palette - Dark & Light Themes
 * Professional, user-friendly colors for healthcare applications
 */

export const colors = {
  // ============================================================================
  // DARK THEME
  // ============================================================================
  dark: {
    // Primary Colors
    primary: '#1E40AF',           // Clinical Blue - Authority & Trust
    secondary: '#059669',         // Healthcare Green - Safety
    accent: '#0D9488',            // Medical Teal - Precision
    
    // Background
    bgPrimary: '#0F172A',         // Hospital Dark
    bgSecondary: '#1E293B',       // Medical Neutral
    bgSurface: '#334155',         // Clinical Surface
    bgCard: '#1E293B',            // Card background
    bgHover: '#334155',           // Hover state
    
    // Text Colors
    textPrimary: '#F1F5F9',       // Primary text
    textSecondary: '#CBD5E1',     // Secondary text
    textMuted: '#94A3B8',         // Muted text
    textDisabled: '#64748B',      // Disabled text
    
    // Medical Diagnostics
    healthy: '#10B981',           // Green - Negative result
    benign: '#3B82F6',            // Blue - Safe finding
    suspicious: '#F59E0B',        // Amber - Review needed
    malignant: '#DC2626',         // Red - Critical alert
    
    // Analysis Visualization
    tumorDetection: '#EF4444',    // Detection markers
    tissueAnalysis: '#8B5CF6',    // Tissue regions
    confidenceScore: '#0EA5E9',   // Algorithm confidence
    riskLevel: '#FBBF24',         // Risk assessment
    
    // UI Elements
    border: '#475569',            // Border color
    divider: '#334155',           // Divider
    shadow: 'rgba(0, 0, 0, 0.5)', // Shadow
    overlay: 'rgba(0, 0, 0, 0.7)',// Modal overlay
    
    // Status Colors
    success: '#10B981',           // Success
    warning: '#F59E0B',           // Warning
    error: '#DC2626',             // Error
    info: '#3B82F6',              // Info
  },
  
  // ============================================================================
  // LIGHT THEME
  // ============================================================================
  light: {
    // Primary Colors
    primary: '#1E40AF',           // Clinical Blue - Authority & Trust
    secondary: '#059669',         // Healthcare Green - Safety
    accent: '#0D9488',            // Medical Teal - Precision
    
    // Background
    bgPrimary: '#FFFFFF',         // Clean Hospital White
    bgSecondary: '#F8FAFC',       // Sterile Off-White
    bgSurface: '#F1F5F9',         // Light Gray
    bgCard: '#FFFFFF',            // Card background
    bgHover: '#F1F5F9',           // Hover state
    
    // Text Colors
    textPrimary: '#0F172A',       // Primary text
    textSecondary: '#475569',     // Secondary text
    textMuted: '#64748B',         // Muted text
    textDisabled: '#94A3B8',      // Disabled text
    
    // Medical Diagnostics (Same as dark)
    healthy: '#059669',           // Green
    benign: '#2563EB',            // Blue
    suspicious: '#D97706',        // Orange
    malignant: '#DC2626',         // Red
    
    // Analysis Visualization
    tumorDetection: '#EF4444',    // Detection markers
    tissueAnalysis: '#8B5CF6',    // Tissue regions
    confidenceScore: '#0EA5E9',   // Algorithm confidence
    riskLevel: '#FBBF24',         // Risk assessment
    
    // UI Elements
    border: '#E2E8F0',            // Border color
    divider: '#CBD5E1',           // Divider
    shadow: 'rgba(0, 0, 0, 0.1)', // Shadow
    overlay: 'rgba(0, 0, 0, 0.5)',// Modal overlay
    
    // Status Colors
    success: '#059669',           // Success
    warning: '#D97706',           // Warning
    error: '#DC2626',             // Error
    info: '#2563EB',              // Info
  }
};

/**
 * Risk level color mapping
 */
export const riskLevelColors = {
  low: {
    dark: '#10B981',
    light: '#059669'
  },
  moderate: {
    dark: '#F59E0B',
    light: '#D97706'
  },
  high: {
    dark: '#EF4444',
    light: '#DC2626'
  },
  very_high: {
    dark: '#DC2626',
    light: '#B91C1C'
  }
};

/**
 * Prediction color mapping
 */
export const predictionColors = {
  benign: {
    dark: '#3B82F6',
    light: '#2563EB'
  },
  malignant: {
    dark: '#DC2626',
    light: '#DC2626'
  }
};

/**
 * Gradient backgrounds
 */
export const gradients = {
  dark: {
    primary: 'linear-gradient(135deg, #1E40AF 0%, #3B82F6 100%)',
    secondary: 'linear-gradient(135deg, #059669 0%, #10B981 100%)',
    accent: 'linear-gradient(135deg, #0D9488 0%, #14B8A6 100%)',
    danger: 'linear-gradient(135deg, #DC2626 0%, #EF4444 100%)',
    success: 'linear-gradient(135deg, #059669 0%, #10B981 100%)',
  },
  light: {
    primary: 'linear-gradient(135deg, #1E40AF 0%, #3B82F6 100%)',
    secondary: 'linear-gradient(135deg, #059669 0%, #10B981 100%)',
    accent: 'linear-gradient(135deg, #0D9488 0%, #14B8A6 100%)',
    danger: 'linear-gradient(135deg, #DC2626 0%, #EF4444 100%)',
    success: 'linear-gradient(135deg, #059669 0%, #10B981 100%)',
  }
};

/**
 * Chart colors
 */
export const chartColors = {
  dark: ['#3B82F6', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6', '#0EA5E9'],
  light: ['#2563EB', '#059669', '#D97706', '#DC2626', '#7C3AED', '#0284C7']
};

export default colors;

