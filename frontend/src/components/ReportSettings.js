/**
 * Report Settings Component
 * Allows doctors to customize PDF report branding with base64 logo storage
 * Enterprise Design System v2.0
 */

import React, { useState, useEffect } from 'react';
import { API_BASE_URL } from '../config/api';
import '../styles/enterpriseDesignSystem.css';
import './ReportSettings.css';

function ReportSettings({ onBack }) {
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);
    const [message, setMessage] = useState({ type: '', text: '' });

    const [settings, setSettings] = useState({
        hospital_name: '',
        doctor_name: '',
        footer_text: '',
        logo_base64: '',
        hospital_address: '',
        hospital_contact: '',
        display_name: '',
        license_number: '',
        report_header_color: '#2563EB',
        report_footer_text: '',
        include_disclaimer: true
    });

    const [logoPreview, setLogoPreview] = useState(null);

    useEffect(() => {
        fetchSettings();
    }, []);

    const fetchSettings = async () => {
        try {
            const response = await fetch(`${API_BASE_URL}/settings`, {
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('token')}`
                }
            });

            if (response.ok) {
                const data = await response.json();
                setSettings(data);
                // Set logo preview from base64 if available
                if (data.logo_base64) {
                    setLogoPreview(data.logo_base64);
                }
            }
        } catch (error) {
            console.error('Error fetching settings:', error);
            setMessage({ type: 'error', text: 'Failed to load settings' });
        } finally {
            setLoading(false);
        }
    };

    const handleInputChange = (e) => {
        const { name, value, type, checked } = e.target;
        setSettings(prev => ({
            ...prev,
            [name]: type === 'checkbox' ? checked : value
        }));
    };

    const handleLogoChange = (e) => {
        const file = e.target.files[0];
        if (file) {
            // Validate file type
            if (!file.type.match(/image\/(png|jpg|jpeg)/)) {
                setMessage({ type: 'error', text: 'Please upload a PNG or JPG image' });
                return;
            }

            // Validate file size (5MB)
            if (file.size > 5 * 1024 * 1024) {
                setMessage({ type: 'error', text: 'Logo file size must be less than 5MB' });
                return;
            }

            // Convert to base64
            const reader = new FileReader();
            reader.onloadend = () => {
                const base64String = reader.result;
                setLogoPreview(base64String);
                setSettings(prev => ({
                    ...prev,
                    logo_base64: base64String
                }));
            };
            reader.readAsDataURL(file);
        }
    };

    const handleSave = async () => {
        setSaving(true);
        setMessage({ type: '', text: '' });

        try {
            // Save settings with base64 logo
            const response = await fetch(`${API_BASE_URL}/settings`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${localStorage.getItem('token')}`
                },
                body: JSON.stringify(settings)
            });

            if (response.ok) {
                setMessage({ type: 'success', text: 'Report settings saved successfully!' });
                // Refresh settings to get updated data
                await fetchSettings();
            } else {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Failed to save settings');
            }
        } catch (error) {
            console.error('Error saving settings:', error);
            setMessage({ type: 'error', text: error.message || 'Failed to save settings. Please try again.' });
        } finally {
            setSaving(false);
        }
    };

    if (loading) {
        return (
            <div className="eds-card" style={{ padding: 'var(--eds-space-8)', textAlign: 'center' }}>
                <div className="loading-spinner"></div>
                <p className="eds-text-body">Loading settings...</p>
            </div>
        );
    }

    return (
        <div className="report-settings-container">
            <div className="eds-card" style={{ padding: 'var(--eds-space-8)' }}>
                <div className="settings-header">
                    <h2 className="eds-heading-2">Report Customization</h2>
                    <p className="eds-text-body" style={{ color: 'var(--eds-color-text-muted)', marginTop: 'var(--eds-space-2)' }}>
                        Customize how your name and hospital information appear on PDF reports
                    </p>
                </div>

                {message.text && (
                    <div className={`message-banner ${message.type}`}>
                        {message.type === 'success' ? '✓' : '⚠'} {message.text}
                    </div>
                )}

                {/* Hospital/Clinic Branding Section */}
                <div className="settings-section">
                    <h3 className="eds-heading-3">Hospital / Clinic Branding</h3>

                    {/* Logo Upload */}
                    <div className="form-group">
                        <label className="eds-label">Hospital Logo</label>
                        <div className="logo-upload-area">
                            <div className="logo-preview-container">
                                {logoPreview ? (
                                    <img src={logoPreview} alt="Hospital Logo" className="logo-preview" />
                                ) : (
                                    <div className="logo-placeholder">
                                        <span className="icon">🏥</span>
                                        <p>No logo uploaded</p>
                                    </div>
                                )}
                            </div>
                            <div className="upload-controls">
                                <input
                                    type="file"
                                    id="logo-upload"
                                    accept=".png,.jpg,.jpeg"
                                    onChange={handleLogoChange}
                                    style={{ display: 'none' }}
                                />
                                <label htmlFor="logo-upload" className="eds-button eds-button-secondary">
                                    📁 Choose Logo
                                </label>
                                <p className="eds-text-small" style={{ marginTop: 'var(--eds-space-2)' }}>
                                    PNG or JPG, max 5MB (stored in database)
                                </p>
                            </div>
                        </div>
                    </div>

                    {/* Hospital Name */}
                    <div className="form-group">
                        <label className="eds-label" htmlFor="hospital_name">Hospital / Clinic Name</label>
                        <input
                            type="text"
                            id="hospital_name"
                            name="hospital_name"
                            className="eds-input"
                            value={settings.hospital_name || ''}
                            onChange={handleInputChange}
                            placeholder="e.g., Apollo Hospitals"
                        />
                    </div>

                    {/* Hospital Address */}
                    <div className="form-group">
                        <label className="eds-label" htmlFor="hospital_address">Address / Contact Info</label>
                        <textarea
                            id="hospital_address"
                            name="hospital_address"
                            className="eds-textarea"
                            rows="3"
                            value={settings.hospital_address || ''}
                            onChange={handleInputChange}
                            placeholder="Full address, phone, email (appears in report footer)"
                        />
                    </div>

                    {/* Hospital Contact */}
                    <div className="form-group">
                        <label className="eds-label" htmlFor="hospital_contact">Contact Number</label>
                        <input
                            type="text"
                            id="hospital_contact"
                            name="hospital_contact"
                            className="eds-input"
                            value={settings.hospital_contact || ''}
                            onChange={handleInputChange}
                            placeholder="e.g., +91 123-456-7890"
                        />
                    </div>
                </div>

                {/* Doctor Details Section */}
                <div className="settings-section">
                    <h3 className="eds-heading-3">Doctor Details</h3>

                    {/* Doctor Name */}
                    <div className="form-group">
                        <label className="eds-label" htmlFor="doctor_name">Doctor Name</label>
                        <input
                            type="text"
                            id="doctor_name"
                            name="doctor_name"
                            className="eds-input"
                            value={settings.doctor_name || ''}
                            onChange={handleInputChange}
                            placeholder="e.g., Dr. Rajesh Sharma"
                        />
                        <p className="eds-text-small" style={{ marginTop: 'var(--eds-space-1)', color: 'var(--eds-color-text-muted)' }}>
                            How your name will appear on reports
                        </p>
                    </div>

                    {/* Display Name */}
                    <div className="form-group">
                        <label className="eds-label" htmlFor="display_name">Display Name (with credentials)</label>
                        <input
                            type="text"
                            id="display_name"
                            name="display_name"
                            className="eds-input"
                            value={settings.display_name || ''}
                            onChange={handleInputChange}
                            placeholder="e.g., Dr. Rajesh Sharma, MD"
                        />
                        <p className="eds-text-small" style={{ marginTop: 'var(--eds-space-1)', color: 'var(--eds-color-text-muted)' }}>
                            Full name with credentials
                        </p>
                    </div>

                    {/* License Number */}
                    <div className="form-group">
                        <label className="eds-label" htmlFor="license_number">License / Registration Number</label>
                        <input
                            type="text"
                            id="license_number"
                            name="license_number"
                            className="eds-input"
                            value={settings.license_number || ''}
                            onChange={handleInputChange}
                            placeholder="e.g., MCI-12345"
                        />
                        <p className="eds-text-small" style={{ marginTop: 'var(--eds-space-1)', color: 'var(--eds-color-text-muted)' }}>
                            Optional: Medical license number
                        </p>
                    </div>
                </div>

                {/* Report Customization Section */}
                <div className="settings-section">
                    <h3 className="eds-heading-3">Report Customization</h3>

                    {/* Footer Text */}
                    <div className="form-group">
                        <label className="eds-label" htmlFor="footer_text">Custom Footer Text</label>
                        <textarea
                            id="footer_text"
                            name="footer_text"
                            className="eds-textarea"
                            rows="3"
                            value={settings.footer_text || ''}
                            onChange={handleInputChange}
                            placeholder="Custom text for report footer (e.g., hospital address, contact info, disclaimer)"
                        />
                        <p className="eds-text-small" style={{ marginTop: 'var(--eds-space-1)', color: 'var(--eds-color-text-muted)' }}>
                            This text will appear at the bottom of every page in the PDF report
                        </p>
                    </div>

                    {/* Header Color */}
                    <div className="form-group">
                        <label className="eds-label" htmlFor="report_header_color">Report Header Color</label>
                        <div className="color-picker-group">
                            <input
                                type="color"
                                id="report_header_color"
                                name="report_header_color"
                                className="color-input"
                                value={settings.report_header_color || '#2563EB'}
                                onChange={handleInputChange}
                            />
                            <input
                                type="text"
                                className="eds-input"
                                value={settings.report_header_color || '#2563EB'}
                                onChange={handleInputChange}
                                name="report_header_color"
                                placeholder="#2563EB"
                                style={{ width: '120px' }}
                            />
                        </div>
                    </div>

                    {/* Include Disclaimer */}
                    <div className="form-group">
                        <label className="checkbox-label">
                            <input
                                type="checkbox"
                                name="include_disclaimer"
                                checked={settings.include_disclaimer || false}
                                onChange={handleInputChange}
                            />
                            <span>Include medical disclaimer in reports</span>
                        </label>
                    </div>
                </div>

                {/* Action Buttons */}
                <div className="settings-actions">
                    <button
                        className="eds-button eds-button-primary"
                        onClick={handleSave}
                        disabled={saving}
                    >
                        {saving ? 'Saving...' : '💾 Save Configuration'}
                    </button>
                    {onBack && (
                        <button
                            className="eds-button eds-button-secondary"
                            onClick={onBack}
                            disabled={saving}
                        >
                            ← Back
                        </button>
                    )}
                </div>
            </div>

            {/* Preview Info */}
            <div className="eds-card" style={{ padding: 'var(--eds-space-6)', marginTop: 'var(--eds-space-6)', background: 'var(--eds-color-info-light)' }}>
                <h4 className="eds-heading-4" style={{ marginBottom: 'var(--eds-space-3)' }}>ℹ️ How This Works</h4>
                <ul className="info-list">
                    <li>Your hospital logo is stored securely in the database and will appear in all PDF reports</li>
                    <li>The doctor name will appear as the report generator</li>
                    <li>Custom footer text replaces the default footer in PDF reports</li>
                    <li>These settings are saved to the database and persist across all devices</li>
                    <li>Changes take effect immediately for new reports</li>
                </ul>
            </div>
        </div>
    );
}

export default ReportSettings;
