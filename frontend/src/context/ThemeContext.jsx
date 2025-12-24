/**
 * Theme Context - Dark/Light Mode Management
 * Provides theme switching functionality across the application
 */

import React, { createContext, useContext, useState, useEffect } from 'react';
import { colors, riskLevelColors, predictionColors, gradients, chartColors } from '../theme/colors';

const ThemeContext = createContext();

export const useTheme = () => {
  const context = useContext(ThemeContext);
  if (!context) {
    throw new Error('useTheme must be used within a ThemeProvider');
  }
  return context;
};

export const ThemeProvider = ({ children }) => {
  // Get initial theme from localStorage or default to 'dark'
  const [theme, setTheme] = useState(() => {
    const savedTheme = localStorage.getItem('theme');
    return savedTheme || 'dark';
  });

  // Update localStorage when theme changes
  useEffect(() => {
    localStorage.setItem('theme', theme);
    
    // Update document root class for global CSS
    document.documentElement.setAttribute('data-theme', theme);
    
    // Apply theme colors to CSS variables
    const themeColors = colors[theme];
    Object.keys(themeColors).forEach((key) => {
      document.documentElement.style.setProperty(
        `--color-${key}`,
        themeColors[key]
      );
    });
  }, [theme]);

  const toggleTheme = () => {
    setTheme((prevTheme) => (prevTheme === 'dark' ? 'light' : 'dark'));
  };

  const getRiskColor = (riskLevel) => {
    const level = riskLevel?.toLowerCase().replace(' ', '_');
    return riskLevelColors[level]?.[theme] || colors[theme].textMuted;
  };

  const getPredictionColor = (prediction) => {
    const pred = prediction?.toLowerCase();
    return predictionColors[pred]?.[theme] || colors[theme].textPrimary;
  };

  const value = {
    theme,
    isDark: theme === 'dark',
    isLight: theme === 'light',
    toggleTheme,
    colors: colors[theme],
    gradients: gradients[theme],
    chartColors: chartColors[theme],
    getRiskColor,
    getPredictionColor,
  };

  return <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>;
};

export default ThemeContext;

