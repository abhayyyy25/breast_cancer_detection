import React, { useState } from 'react';
import './DisclaimerModal.css';

/**
 * Compliance Disclaimer Modal
 * 
 * Forces doctors to acknowledge that AI analysis is assistive only,
 * not a replacement for medical judgment.
 * 
 * HIPAA/Medical Compliance Requirement.
 */
const DisclaimerModal = ({ isOpen, onAccept, onDecline, patientName }) => {
  const [hasReadFully, setHasReadFully] = useState(false);
  const [userConfirmation, setUserConfirmation] = useState('');

  if (!isOpen) return null;

  const handleAccept = () => {
    const normalizedInput = userConfirmation.trim().toLowerCase();
    if (hasReadFully && normalizedInput === 'i understand') {
      // Reset state before calling onAccept
      setHasReadFully(false);
      setUserConfirmation('');
      onAccept();
    }
  };

  const isAcceptEnabled = hasReadFully && userConfirmation.trim().toLowerCase() === 'i understand';

  return (
    <div className="disclaimer-modal-overlay">
      <div className="disclaimer-modal">
        <div className="disclaimer-header">
          <div className="disclaimer-icon">⚠️</div>
          <h2>Medical Disclaimer & AI Limitations</h2>
        </div>

        <div className="disclaimer-content">
          <div className="disclaimer-section">
            <h3>🤖 AI-Assisted Diagnosis Notice</h3>
            <p>
              This system uses artificial intelligence to <strong>assist</strong> in breast cancer detection.
              The AI analysis is <strong>NOT</strong> a definitive diagnosis.
            </p>
          </div>

          <div className="disclaimer-section warning-box">
            <h3>⚕️ Medical Professional Responsibility</h3>
            <ul>
              <li>You, as the licensed medical professional, are ultimately responsible for all diagnostic decisions</li>
              <li>AI predictions must be verified through standard clinical protocols</li>
              <li>This tool does not replace radiologist expertise, biopsy, or other confirmatory tests</li>
              <li>False positives and false negatives can occur with any AI system</li>
            </ul>
          </div>

          <div className="disclaimer-section">
            <h3>📋 Clinical Workflow Requirements</h3>
            <ul>
              <li>Review the complete patient medical history before making decisions</li>
              <li>Correlate AI findings with clinical examination and other diagnostic tests</li>
              <li>Follow established institutional protocols for breast cancer screening</li>
              <li>Document your clinical reasoning independently of AI suggestions</li>
            </ul>
          </div>

          <div className="disclaimer-section">
            <h3>🔒 Compliance & Liability</h3>
            <ul>
              <li>This analysis will be logged for audit purposes (HIPAA compliance)</li>
              <li>Patient consent must be obtained per institutional policy</li>
              <li>You acknowledge that you are qualified to interpret these results</li>
              <li>The AI is a decision-support tool, not a medical device</li>
            </ul>
          </div>

          {patientName && (
            <div className="patient-info-box">
              <strong>Patient:</strong> {patientName}
            </div>
          )}

          <div className="disclaimer-section confirmation-section">
            <label className="disclaimer-checkbox">
              <input
                type="checkbox"
                checked={hasReadFully}
                onChange={(e) => setHasReadFully(e.target.checked)}
              />
              <span>
                I have read and understood the above disclaimer in its entirety
              </span>
            </label>

            <div className="confirmation-input-group">
              <label htmlFor="confirmation-input">
                Type "<strong>I understand</strong>" to proceed:
              </label>
              <input
                id="confirmation-input"
                type="text"
                value={userConfirmation}
                onChange={(e) => setUserConfirmation(e.target.value)}
                placeholder="Type here..."
                disabled={!hasReadFully}
                className="confirmation-input"
              />
            </div>
          </div>
        </div>

        <div className="disclaimer-actions">
          <button
            className="btn-decline"
            onClick={onDecline}
          >
            Cancel Scan
          </button>
          <button
            className="btn-accept"
            onClick={handleAccept}
            disabled={!isAcceptEnabled}
          >
            Proceed with Analysis
          </button>
        </div>

        <div className="disclaimer-footer">
          <small>
            Version 2.0.0 | Last Updated: December 2024 | 
            For Medical Professionals Only
          </small>
        </div>
      </div>
    </div>
  );
};

export default DisclaimerModal;

