/**
 * Report Settings Component
 * Allows doctors to customize PDF report branding
 * Enterprise Design System v2.0
 */

import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import '../styles/enterpriseDesignSystem.css';
import './ReportSettings.css';

const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://localhost:8000';

function ReportSettings({ onBack }) {
    const { user } = useAuth();
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);
    const [message, setMessage] = useState({ type: '', text: '' });

    const [settings, setSettings] = useState({
        hospital_name: '',
        hospital_logo_url: '',
        hospital_address: '',
        hospital_contact: '',
        display_name: '',
        license_number: '',
        signature_url: '',
        report_header_color: '#2563EB',
        report_footer_text: '',
        include_disclaimer: true
    });

    const [logoFile, setLogoFile] = useState(null);
    const [logoPreview, setLogoPreview] = useState(null);
    const [signatureFile, setSignatureFile] = useState(null);
    const [signaturePreview, setSignaturePreview] = useState(null);

    useEffect(() => {
        fetchSettings();
    }, []);

    const fetchSettings = async () => {
        try {
            const response = await fetch(`${API_BASE_URL}/api/report-settings`, {
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('token')}`
                }
            });

            if (response.ok) {
                const data = await response.json();
                setSettings(data);
                if (data.hospital_logo_url) {
                    setLogoPreview(`${API_BASE_URL}${data.hospital_logo_url}`);
                }
                if (data.signature_url) {
                    setSignaturePreview(`${API_BASE_URL}${data.signature_url}`);
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

            setLogoFile(file);
            setLogoPreview(URL.createObjectURL(file));
        }
    };

    const handleSignatureChange = (e) => {
        const file = e.target.files[0];
        if (file) {
            // Validate file type
            if (!file.type.match(/image\/(png|jpg|jpeg)/)) {
                setMessage({ type: 'error', text: 'Please upload a PNG or JPG image' });
                return;
            }

            // Validate file size (2MB)
            if (file.size > 2 * 1024 * 1024) {
                setMessage({ type: 'error', text: 'Signature file size must be less than 2MB' });
                return;
            }

            setSignatureFile(file);
            setSignaturePreview(URL.createObjectURL(file));
        }
    };

    const uploadLogo = async () => {
        if (!logoFile) return;

        const formData = new FormData();
        formData.append('file', logoFile);

        try {
            const response = await fetch(`${API_BASE_URL}/api/report-settings/upload-logo`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('token')}`
                },
                body: formData
            });

            if (response.ok) {
                const data = await response.json();
                setSettings(prev => ({ ...prev, hospital_logo_url: data.logo_url }));
                return true;
            } else {
                throw new Error('Logo upload failed');
            }
        } catch (error) {
            console.error('Error uploading logo:', error);
            throw error;
        }
    };

    const uploadSignature = async () => {
        if (!signatureFile) return;

        const formData = new FormData();
        formData.append('file', signatureFile);

        try {
            const response = await fetch(`${API_BASE_URL}/api/report-settings/upload-signature`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('token')}`
                },
                body: formData
            });

            if (response.ok) {
                const data = await response.json();
                setSettings(prev => ({ ...prev, signature_url: data.signature_url }));
                return true;
            } else {
                throw new Error('Signature upload failed');
            }
        } catch (error) {
            console.error('Error uploading signature:', error);
            throw error;
        }
    };

    const handleSave = async () => {
        setSaving(true);
        setMessage({ type: '', text: '' });

        try {
            // Upload logo if changed
            if (logoFile) {
                await uploadLogo();
            }

            // Upload signature if changed
            if (signatureFile) {
                await uploadSignature();
            }

            // Save settings
            const response = await fetch(`${API_BASE_URL}/api/report-settings`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${localStorage.getItem('token')}`
                },
                body: JSON.stringify(settings)
            });

            if (response.ok) {
                setMessage({ type: 'success', text: 'Report settings saved successfully!' });
                setLogoFile(null);
                setSignatureFile(null);
            } else {
                throw new Error('Failed to save settings');
            }
        } catch (error) {
            console.error('Error saving settings:', error);
            setMessage({ type: 'error', text: 'Failed to save settings. Please try again.' });
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
                                    PNG or JPG, max 5MB
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
                            value={settings.hospital_name}
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
                            value={settings.hospital_address}
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
                            value={settings.hospital_contact}
                            onChange={handleInputChange}
                            placeholder="e.g., +91 123-456-7890"
                        />
                    </div>
                </div>

                {/* Doctor Details Section */}
                <div className="settings-section">
                    <h3 className="eds-heading-3">Doctor Details (Default)</h3>

                    {/* Display Name */}
                    <div className="form-group">
                        <label className="eds-label" htmlFor="display_name">Display Name</label>
                        <input
                            type="text"
                            id="display_name"
                            name="display_name"
                            className="eds-input"
                            value={settings.display_name}
                            onChange={handleInputChange}
                            placeholder="e.g., Dr. Rajesh Sharma, MD"
                        />
                        <p className="eds-text-small" style={{ marginTop: 'var(--eds-space-1)', color: 'var(--eds-color-text-muted)' }}>
                            How your name will appear on reports
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
                            value={settings.license_number}
                            onChange={handleInputChange}
                            placeholder="e.g., MCI-12345"
                        />
                        <p className="eds-text-small" style={{ marginTop: 'var(--eds-space-1)', color: 'var(--eds-color-text-muted)' }}>
                            Optional: Appears below signature
                        </p>
                    </div>

                    {/* Signature Upload (Only for Doctors) */}
                    {user?.role === 'doctor' && (
                        <div className="form-group">
                            <label className="eds-label">Digital Signature</label>
                            <div className="signature-upload-area">
                                <div className="signature-preview-container">
                                    {signaturePreview ? (
                                        <img src={signaturePreview} alt="Signature" className="signature-preview" />
                                    ) : (
                                        <div className="signature-placeholder">
                                            <span className="icon">✍️</span>
                                            <p>No signature uploaded</p>
                                        </div>
                                    )}
                                </div>
                                <div className="upload-controls">
                                    <input
                                        type="file"
                                        id="signature-upload"
                                        accept=".png,.jpg,.jpeg"
                                        onChange={handleSignatureChange}
                                        style={{ display: 'none' }}
                                    />
                                    <label htmlFor="signature-upload" className="eds-button eds-button-secondary">
                                        ✍️ Choose Signature
                                    </label>
                                    <p className="eds-text-small" style={{ marginTop: 'var(--eds-space-2)' }}>
                                        PNG or JPG, max 2MB
                                    </p>
                                </div>
                            </div>
                        </div>
                    )}
                </div>

                {/* Report Customization Section */}
                <div className="settings-section">
                    <h3 className="eds-heading-3">Report Customization</h3>

                    {/* Header Color */}
                    <div className="form-group">
                        <label className="eds-label" htmlFor="report_header_color">Report Header Color</label>
                        <div className="color-picker-group">
                            <input
                                type="color"
                                id="report_header_color"
                                name="report_header_color"
                                className="color-input"
                                value={settings.report_header_color}
                                onChange={handleInputChange}
                            />
                            <input
                                type="text"
                                className="eds-input"
                                value={settings.report_header_color}
                                onChange={handleInputChange}
                                name="report_header_color"
                                placeholder="#2563EB"
                                style={{ width: '120px' }}
                            />
                        </div>
                    </div>

                    {/* Footer Text */}
                    <div className="form-group">
                        <label className="eds-label" htmlFor="report_footer_text">Custom Footer Text</label>
                        <textarea
                            id="report_footer_text"
                            name="report_footer_text"
                            className="eds-textarea"
                            rows="2"
                            value={settings.report_footer_text}
                            onChange={handleInputChange}
                            placeholder="Optional custom text for report footer"
                        />
                    </div>

                    {/* Include Disclaimer */}
                    <div className="form-group">
                        <label className="checkbox-label">
                            <input
                                type="checkbox"
                                name="include_disclaimer"
                                checked={settings.include_disclaimer}
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
                    <li>Your hospital logo will appear in the header of all PDF reports you generate</li>
                    <li>The display name will replace "Dr. [Name]" placeholders in reports</li>
                    <li>Hospital address and contact info will appear in the report footer</li>
                    <li>These settings apply only to reports you generate</li>
                    <li>Changes take effect immediately for new reports</li>
                </ul>
            </div>
        </div>
    );
}

export default ReportSettings;
