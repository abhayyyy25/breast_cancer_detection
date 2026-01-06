// This file contains the original App logic
// Renamed from App.js to AppContent.js to avoid confusion

import React, { useMemo, useState } from "react";
import "./App.css";
import { FiUploadCloud, FiLogOut } from "react-icons/fi";
import { useAuth } from "./context/AuthContext";
import { useNavigate } from "react-router-dom";

const getDefaultApiBase = () => {
  // Check for environment variable first (for production deployment)
  const envUrl = process.env.REACT_APP_API_BASE_URL;
  if (envUrl && envUrl.trim().length > 0) {
    console.log("Using API URL from env:", envUrl);
    return envUrl.replace(/\/$/, "");
  }

  // For local development
  if (typeof window !== "undefined") {
    const localHosts = ["localhost", "127.0.0.1", "0.0.0.0"];
    if (localHosts.includes(window.location.hostname)) {
      console.log("Using local API URL: http://localhost:8000");
      return "http://localhost:8000";
    }
  }

  // Fallback for production (Render backend)
  // IMPORTANT: Update this URL to your deployed backend URL
  const productionUrl = "https://breast-cancer-73t1.onrender.com";
  console.log("Using production API URL:", productionUrl);
  return productionUrl;
};

const buildEndpoint = (base, endpoint) => {
  const safeBase = base.endsWith("/") ? base.slice(0, -1) : base;
  const safeEndpoint = endpoint.startsWith("/") ? endpoint : `/${endpoint}`;
  return `${safeBase}${safeEndpoint}`;
};

const asDataUrl = (value) => (value ? `data:image/png;base64,${value}` : null);

function AppContent() {
  const apiBase = useMemo(() => getDefaultApiBase(), []);
  const apiUrl = (endpoint) => buildEndpoint(apiBase, endpoint);
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const [results, setResults] = useState({});
  const [file, setFile] = useState(null);
  const [dragActive, setDragActive] = useState(false);
  const [analysisDone, setAnalysisDone] = useState(false);
  const [visualTab, setVisualTab] = useState("overlay");
  const [detailsTab, setDetailsTab] = useState("model");
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [isGeneratingReport, setIsGeneratingReport] = useState(false);
  const [statusMessage, setStatusMessage] = useState("");
  const [errorMessage, setErrorMessage] = useState("");

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      const selectedFile = e.target.files[0];
      setFile(selectedFile);
      analyzeFile(selectedFile);
    }
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    setDragActive(true);
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    setDragActive(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const droppedFile = e.dataTransfer.files[0];
      setFile(droppedFile);
      analyzeFile(droppedFile);
    }
  };

  const handleBrowseClick = () => {
    const input = document.getElementById("fileInput");
    if (input) input.click();
  };

  const handleBackToUpload = () => {
    setAnalysisDone(false);
    setResults({});
    setFile(null);
    setVisualTab("overlay");
    setDetailsTab("model");
    setStatusMessage("");
    setErrorMessage("");
  };

  const analyzeFile = async (selectedFile) => {
    if (!selectedFile) return;
    const formData = new FormData();
    formData.append("file", selectedFile);

    setIsAnalyzing(true);
    setStatusMessage("Uploading image for analysis…");
    setErrorMessage("");

    const currentApiUrl = apiUrl("/analyze");
    console.log("Sending request to:", currentApiUrl);

    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 120000); // 2 minute timeout

      const response = await fetch(currentApiUrl, {
        method: "POST",
        body: formData,
        signal: controller.signal,
      });

      clearTimeout(timeoutId);

      if (!response.ok) {
        const errorBody = await response.json().catch(() => ({}));
        console.error("API Error:", response.status, errorBody);
        throw new Error(errorBody.detail || `Server error: ${response.status}`);
      }

      const data = await response.json();
      const images = data.images || {};
      const confidencePercent =
        data.confidence !== undefined && data.confidence <= 1
          ? data.confidence * 100
          : data.confidence ?? null;

      const resultData = {
        original: asDataUrl(images.original),
        overlay: asDataUrl(images.overlay),
        heatmap: asDataUrl(images.heatmap_only),
        bbox: asDataUrl(images.bbox),
        malignant: data.malignant_prob ?? null,
        benign: data.benign_prob ?? null,
        risk: data.risk_level ?? "Unavailable",
        riskIcon: data.risk_icon,
        riskColor: data.risk_color,
        result: data.result ?? "Analysis Result",
        confidence: confidencePercent,
        rawScore: data.confidence ?? null,
        threshold: data.threshold ?? 0.5,
        stats: data.stats || {},
        findings: data.findings || null,  // NEW: Detailed findings from backend
      };

      // Debug logging
      console.log("Analysis Results:", {
        result: resultData.result,
        riskLevel: resultData.risk,
        malignantProb: resultData.malignant,
        benignProb: resultData.benign,
        confidence: resultData.confidence
      });

      setResults(resultData);

      setAnalysisDone(true);
      setVisualTab("overlay");
      setDetailsTab("model");
      setStatusMessage("Analysis complete.");
    } catch (error) {
      console.error("Analysis error:", error);

      let errorMsg = "Backend not reachable.";

      if (error.name === 'AbortError') {
        errorMsg = "Request timed out. The backend server may be starting up (this can take 1-2 minutes on free hosting). Please try again.";
      } else if (error.message.includes('Failed to fetch') || error.message.includes('NetworkError')) {
        errorMsg = `Cannot connect to backend at ${apiBase}. Please check if the backend is running and CORS is enabled.`;
      } else if (error.message) {
        errorMsg = error.message;
      }

      setErrorMessage(errorMsg);
      setStatusMessage("");
    } finally {
      setIsAnalyzing(false);
    }
  };

  const handleDownloadReport = async () => {
    if (!file) {
      setErrorMessage("Please upload a file before requesting the report.");
      return;
    }

    const formData = new FormData();
    formData.append("file", file);
    setIsGeneratingReport(true);
    setErrorMessage("");

    try {
      const response = await fetch(apiUrl("/report"), {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        const errorBody = await response.json().catch(() => ({}));
        throw new Error(errorBody.detail || "Failed to generate report.");
      }

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const anchor = document.createElement("a");
      anchor.href = url;
      anchor.download = "breast_cancer_report.pdf";
      document.body.appendChild(anchor);
      anchor.click();
      anchor.remove();
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error(error);
      setErrorMessage(error.message || "Error while downloading report.");
    } finally {
      setIsGeneratingReport(false);
    }
  };

  const getActiveVisualImage = () => {
    switch (visualTab) {
      case "heatmap":
        return results.heatmap;
      case "bbox":
        return results.bbox;
      case "original":
        return results.original;
      case "overlay":
      default:
        return results.overlay;
    }
  };

  const getRiskClass = () => {
    const risk = results.risk?.toLowerCase() || "";
    // Check in order from most specific to least specific
    if (risk.includes("very high risk")) {
      return "risk-high";
    } else if (risk.includes("high risk") && !risk.includes("moderate")) {
      return "risk-high";
    } else if (risk.includes("moderate")) {
      return "risk-moderate";
    } else if (risk.includes("very low risk")) {
      return "risk-low";
    } else if (risk.includes("low risk")) {
      return "risk-low";
    }
    return "";
  };

  const getResultClass = () => {
    const result = results.result?.toLowerCase() || "";
    if (result.includes("malignant") || result.includes("cancerous")) {
      return "result-malignant";
    } else if (result.includes("benign") || result.includes("non-cancerous")) {
      return "result-benign";
    }
    return "";
  };

  return (
    <div className="App">
      <video autoPlay muted loop id="bg-video">
        <source src="/backgroundpink.mp4" type="video/mp4" />
      </video>
      <div className="bg-overlay" />

      <header className="header">
        <div className="logo">
          <img src="/Group 28.png" alt="logo" />
          <span>Breast Cancer Detection</span>
        </div>
        <div className="header-right">
          <span className="welcome-text">Welcome, {user?.name || 'User'}</span>
          <button className="logout-btn" onClick={handleLogout}>
            <FiLogOut size={16} />
            Logout
          </button>
        </div>
      </header>

      {!analysisDone ? (
        <section className="upload-section">
          <div className="upload-card">
            <h3>Upload mammogram (DICOM)</h3>
            <p>Max 200MB • Supported formats: DICOM</p>
            <div
              className={`dropzone ${dragActive ? "active" : ""}`}
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              onDrop={handleDrop}
              onClick={handleBrowseClick}
            >
              <FiUploadCloud
                size={50}
                style={{ color: "#AE70AF", marginBottom: "10px" }}
              />
              <p className="drop-main-text">
                {isAnalyzing ? "Analyzing…" : "Drag & drop file here"}
              </p>
              <p className="drop-sub-text">or click to browse files</p>
              <button
                type="button"
                className="btn-primary"
                onClick={(event) => {
                  event.stopPropagation();
                  handleBrowseClick();
                }}
                disabled={isAnalyzing}
              >
                {isAnalyzing ? "Processing…" : "Browse File"}
              </button>
              <input
                type="file"
                id="fileInput"
                style={{ display: "none" }}
                onChange={handleFileChange}
                accept=".jpg,.jpeg,.png,.dcm"
                disabled={isAnalyzing}
              />
            </div>

            {file && (
              <p className="selected-file">
                Selected File: <strong>{file.name}</strong>
              </p>
            )}
            {statusMessage && (
              <p className="muted small" style={{ marginTop: "10px" }}>
                {statusMessage}
              </p>
            )}
            {errorMessage && (
              <p className="muted small" style={{ color: "#ff8080" }}>
                {errorMessage}
              </p>
            )}
          </div>
        </section>
      ) : (
        <main className="analysis-container">
          <section className="analysis-card">
            <div className="result-header">
              <h2 className={`result-title ${getResultClass()}`}>
                {results.result || "Analysis Result"}
              </h2>
              <p className={`risk-pill ${getRiskClass()}`}>
                Risk Level:&nbsp;
                <strong>
                  {results.risk || "Not available"}
                </strong>
              </p>
            </div>

            {errorMessage && (
              <div style={{ marginBottom: "15px" }}>
                <p className="muted small" style={{ color: "#ff8080" }}>
                  {errorMessage}
                </p>
              </div>
            )}

            <section className="section">
              <h3 className="section-title">Prediction Metrics</h3>
              <div className="metric-grid">
                <div className="metric">
                  <span className="metric-label">Benign</span>
                  <h3>
                    {results.benign != null
                      ? `${results.benign.toFixed(2)}%`
                      : "—"}
                  </h3>
                </div>
                <div className="metric">
                  <span className="metric-label">Malignant</span>
                  <h3>
                    {results.malignant != null
                      ? `${results.malignant.toFixed(2)}%`
                      : "—"}
                  </h3>
                </div>
                <div className="metric">
                  <span className="metric-label">Model Confidence</span>
                  <h3>
                    {results.confidence != null
                      ? `${results.confidence.toFixed(2)}%`
                      : "—"}
                  </h3>
                </div>
              </div>
            </section>

            <section className="section">
              <h3 className="section-title">Visual Analysis</h3>
              <p className="section-subtitle">
                Grad-CAM attention maps showing which regions influenced the
                model&apos;s decision.
              </p>

              <div className="visual-tabs">
                <button
                  className={`visual-tab ${visualTab === "overlay" ? "active" : ""
                    }`}
                  onClick={() => setVisualTab("overlay")}
                >
                  Heatmap Overlay
                </button>
                <button
                  className={`visual-tab ${visualTab === "heatmap" ? "active" : ""
                    }`}
                  onClick={() => setVisualTab("heatmap")}
                >
                  Heatmap Only
                </button>
                <button
                  className={`visual-tab ${visualTab === "bbox" ? "active" : ""}`}
                  onClick={() => setVisualTab("bbox")}
                >
                  Region Detection (BBox)
                </button>
                <button
                  className={`visual-tab ${visualTab === "original" ? "active" : ""
                    }`}
                  onClick={() => setVisualTab("original")}
                >
                  Original Image
                </button>
              </div>

              <div className="visual-panel">
                <div className="visual-image-card">
                  {getActiveVisualImage() ? (
                    <img src={getActiveVisualImage()} alt="Visual analysis" />
                  ) : (
                    <p className="muted small">Image not available.</p>
                  )}
                </div>


                {/* Detailed Analysis Information */}
                <div className="results-info-card">
                  <h4 style={{ textAlign: 'center' }}>Understanding Your Results</h4>

                  {results.result?.toLowerCase().includes("malignant") ? (
                    <div>
                      {/* Detected Regions */}
                      {results.findings?.regions && results.findings.regions.length > 0 && (
                        <>
                          <p className="regions-header">
                            🎯 Detected Regions ({results.findings.num_regions})
                          </p>
                          <div className="regions-grid">
                            {results.findings.regions.map((region, idx) => (
                              <div key={idx} className="region-card">
                                <div className="region-card-header">
                                  📍 Region {region.id}: {region.location?.description || 'Unknown'}
                                </div>
                                <div className="region-card-grid">
                                  <div><span>Confidence:</span> <strong>{region.confidence?.toFixed(1)}%</strong></div>
                                  <div><span>Shape:</span> <strong>{region.shape || '—'}</strong></div>
                                  <div><span>Pattern:</span> <strong>{region.characteristics?.pattern || '—'}</strong></div>
                                  <div>
                                    <span>Severity:</span>{' '}
                                    <span className={`severity-badge ${region.characteristics?.severity || 'low'}`}>
                                      {region.characteristics?.severity || 'low'}
                                    </span>
                                  </div>
                                  <div><span>Area:</span> <strong>{region.size?.area_percentage?.toFixed(2)}%</strong></div>
                                  <div><span>Quadrant:</span> <strong>{region.location?.quadrant || '—'}</strong></div>
                                </div>
                              </div>
                            ))}
                          </div>
                        </>
                      )}

                      <div className="urgent-box malignant">
                        <h5>⚕️ Recommended Action</h5>
                        <p>Based on these findings, consultation with an oncologist or breast specialist is strongly recommended.</p>
                        <ul className="checklist">
                          <li>Clinical Breast Examination</li>
                          <li>Diagnostic Mammography</li>
                          <li>Breast Ultrasound</li>
                          <li>Core Needle Biopsy (if needed)</li>
                        </ul>
                      </div>
                    </div>
                  ) : (
                    <div>
                      <div className="urgent-box" style={{ background: 'linear-gradient(135deg, #f0fdf4 0%, #dcfce7 100%)', border: '1px solid #bbf7d0' }}>
                        <h5 style={{ color: '#059669' }}>✓ Continue Preventive Care</h5>
                        <p>The analysis shows patterns consistent with healthy tissue. Continue regular screenings.</p>
                        <ul className="checklist" style={{ listStyle: 'none' }}>
                          <li style={{ color: '#059669' }}>Monthly self-breast examinations</li>
                          <li style={{ color: '#059669' }}>Age-appropriate mammogram schedules</li>
                          <li style={{ color: '#059669' }}>Report any new changes immediately</li>
                        </ul>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            </section>

            <section className="section">
              <h3 className="section-title">Model & Risk Details</h3>
              <div className="details-tabs">
                <button
                  className={`details-tab ${detailsTab === "model" ? "active" : ""
                    }`}
                  onClick={() => setDetailsTab("model")}
                >
                  Model Information
                </button>
                <button
                  className={`details-tab ${detailsTab === "risk" ? "active" : ""
                    }`}
                  onClick={() => setDetailsTab("risk")}
                >
                  Risk Guide
                </button>
                <button
                  className={`details-tab ${detailsTab === "heatmapInfo" ? "active" : ""
                    }`}
                  onClick={() => setDetailsTab("heatmapInfo")}
                >
                  Heatmap Tips
                </button>
                <button
                  className={`details-tab ${detailsTab === "clinical" ? "active" : ""
                    }`}
                  onClick={() => setDetailsTab("clinical")}
                >
                  Clinical Context
                </button>
                <button
                  className={`details-tab ${detailsTab === "nextSteps" ? "active" : ""
                    }`}
                  onClick={() => setDetailsTab("nextSteps")}
                >
                  Next Steps
                </button>
              </div>

              <div className="details-panel">
                {detailsTab === "model" && (
                  <div>
                    <h4 className="details-heading">⚙️ Model Information</h4>
                    <ul className="details-list">
                      <li><strong>Type:</strong> Convolutional Neural Network (CNN)</li>
                      <li><strong>Input Size:</strong> 224 × 224 × 3 (RGB)</li>
                      <li><strong>Output:</strong> Binary classification (Sigmoid)</li>
                      <li><strong>Visualization:</strong> Grad-CAM attention maps</li>
                      <li><strong>Framework:</strong> TensorFlow/Keras</li>
                    </ul>
                  </div>
                )}
                {detailsTab === "risk" && (
                  <div>
                    <h4 className="details-heading">Risk Assessment Guide</h4>
                    <ul className="details-list">
                      <li><strong>Very Low Risk (0–10%):</strong> Minimal concern. Continue routine annual screenings.</li>
                      <li><strong>Low Risk (10–25%):</strong> Low probability of malignancy. Regular monitoring recommended.</li>
                      <li><strong>Moderate Risk (25–50%):</strong> Some concerning features detected. Additional imaging may be needed.</li>
                      <li><strong>High Risk (50–75%):</strong> Significant abnormalities present. Immediate follow-up with specialist recommended.</li>
                      <li><strong>Very High Risk (75–100%):</strong> Strong indicators of malignancy. Urgent consultation with oncologist required.</li>
                    </ul>
                    <div style={{ marginTop: '16px', padding: '12px', background: 'rgba(255, 200, 220, 0.15)', borderRadius: '8px' }}>
                      <p style={{ fontSize: '0.9rem', margin: 0 }}>
                        <strong>Note:</strong> Risk levels are based on AI model confidence. They should be confirmed with
                        clinical examination, additional imaging (mammography, ultrasound, MRI), and if necessary, tissue biopsy.
                      </p>
                    </div>
                  </div>
                )}
                {detailsTab === "heatmapInfo" && (
                  <div>
                    <h4 className="details-heading">Understanding Grad-CAM Heatmaps</h4>
                    <p style={{ marginBottom: '16px', lineHeight: '1.8' }}>
                      Grad-CAM (Gradient-weighted Class Activation Mapping) is an AI visualization technique that shows
                      which parts of the image most influenced the model's decision. Think of it as the AI "highlighting"
                      areas it found most important.
                    </p>

                    <h4 className="details-heading" style={{ marginTop: '20px' }}>Color Meanings</h4>
                    <ul className="details-list">
                      <li><strong style={{ color: '#DC2626' }}>Red/Orange:</strong> Highest attention areas. The model
                        found these regions most significant for its prediction. In malignant cases, these often indicate
                        suspicious tissue patterns.</li>
                      <li><strong style={{ color: '#F59E0B' }}>Yellow:</strong> Moderate attention. Areas of interest
                        but less critical than red zones.</li>
                      <li><strong style={{ color: '#10B981' }}>Green:</strong> Low to moderate attention. Normal or
                        less concerning tissue patterns.</li>
                      <li><strong style={{ color: '#3B82F6' }}>Blue:</strong> Minimal attention. Areas that had little
                        impact on the final prediction.</li>
                    </ul>

                    <h4 className="details-heading" style={{ marginTop: '20px' }}>Viewing Modes Explained</h4>
                    <ul className="details-list">
                      <li><strong>Heatmap Overlay:</strong> Best for understanding suspicious areas in anatomical context.
                        The original image is shown with colored heatmap overlaid.</li>
                      <li><strong>Heatmap Only:</strong> Pure activation visualization without the original image.
                        Useful for seeing the exact intensity distribution.</li>
                      <li><strong>Region Detection (BBox):</strong> Shows detected regions of interest with bounding boxes.
                        Highlights specific areas the model identified.</li>
                      <li><strong>Original Image:</strong> Unprocessed scan for reference and comparison.</li>
                    </ul>

                    <div style={{ marginTop: '16px', padding: '12px', background: 'rgba(255, 200, 220, 0.15)', borderRadius: '8px' }}>
                      <p style={{ fontSize: '0.9rem', margin: 0 }}>
                        <strong>Important:</strong> Heatmaps show AI attention, not confirmed disease. Red areas don't
                        automatically mean cancer, and blue areas don't guarantee health. Medical professionals use multiple
                        diagnostic tools for accurate assessment.
                      </p>
                    </div>
                  </div>
                )}
                {detailsTab === "clinical" && (
                  <div>
                    <h4 className="details-heading" style={{ textAlign: 'left', fontSize: '1.3rem', marginBottom: '25px', color: '#9C2B6D' }}>Your Image Analysis Details</h4>

                    {/* Summary Card */}
                    <div style={{
                      padding: '20px',
                      background: results.result?.toLowerCase().includes("malignant")
                        ? 'linear-gradient(135deg, #ffe5e5 0%, #fff5f5 100%)'
                        : 'linear-gradient(135deg, #e5fff5 0%, #f5fffa 100%)',
                      borderRadius: '16px',
                      border: `2px solid ${results.result?.toLowerCase().includes("malignant") ? '#ffc9c9' : '#c9ffe5'}`,
                      marginBottom: '25px',
                      boxShadow: '0 2px 8px rgba(0,0,0,0.06)'
                    }}>
                      <p style={{ margin: 0, fontSize: '1.05rem', fontWeight: '700', marginBottom: '10px', color: '#9C2B6D', letterSpacing: '0.3px' }}>
                        AI Summary
                      </p>
                      <p style={{ margin: 0, fontSize: '0.95rem', lineHeight: '1.6', color: '#444' }}>
                        {results.findings?.summary || "Analysis summary not available."}
                      </p>
                    </div>

                    {/* Detection Statistics Table */}
                    <h4 className="details-heading" style={{ marginTop: '30px', marginBottom: '15px', fontSize: '1.15rem', color: '#9C2B6D' }}>Detection Statistics</h4>
                    <div style={{ overflowX: 'auto', background: 'white', borderRadius: '16px', boxShadow: '0 2px 12px rgba(156, 43, 109, 0.08)', padding: '5px' }}>
                      <table style={{ width: '100%', borderCollapse: 'separate', borderSpacing: '0', fontSize: '0.9rem', marginBottom: '0' }}>
                        <thead>
                          <tr style={{ background: 'linear-gradient(135deg, #fce7f3 0%, #fbcfe8 100%)' }}>
                            <th style={{ padding: '14px 16px', textAlign: 'left', borderBottom: 'none', fontWeight: '700', color: '#9C2B6D', borderTopLeftRadius: '12px' }}>Metric</th>
                            <th style={{ padding: '14px 16px', textAlign: 'left', borderBottom: 'none', fontWeight: '700', color: '#9C2B6D' }}>Value</th>
                            <th style={{ padding: '14px 16px', textAlign: 'left', borderBottom: 'none', fontWeight: '700', color: '#9C2B6D', borderTopRightRadius: '12px' }}>Description</th>
                          </tr>
                        </thead>
                        <tbody>
                          <tr style={{ background: 'rgba(252, 231, 243, 0.3)' }}>
                            <td style={{ padding: '14px 16px', borderBottom: '1px solid rgba(156, 43, 109, 0.1)', fontWeight: '600', color: '#555' }}>Regions Detected</td>
                            <td style={{ padding: '14px 16px', borderBottom: '1px solid rgba(156, 43, 109, 0.1)', fontWeight: '700', color: '#9C2B6D', fontSize: '1rem' }}>{results.findings?.num_regions || 0}</td>
                            <td style={{ padding: '14px 16px', borderBottom: '1px solid rgba(156, 43, 109, 0.1)', color: '#666' }}>Number of suspicious areas identified</td>
                          </tr>
                          <tr style={{ background: 'white' }}>
                            <td style={{ padding: '14px 16px', borderBottom: '1px solid rgba(156, 43, 109, 0.1)', fontWeight: '600', color: '#555' }}>High-Attention Areas</td>
                            <td style={{ padding: '14px 16px', borderBottom: '1px solid rgba(156, 43, 109, 0.1)', fontWeight: '700', color: '#9C2B6D', fontSize: '1rem' }}>{results.findings?.high_attention_percentage?.toFixed(2) || '0.00'}%</td>
                            <td style={{ padding: '14px 16px', borderBottom: '1px solid rgba(156, 43, 109, 0.1)', color: '#666' }}>Percentage of image with high AI activation</td>
                          </tr>
                          <tr style={{ background: 'rgba(252, 231, 243, 0.3)' }}>
                            <td style={{ padding: '14px 16px', borderBottom: '1px solid rgba(156, 43, 109, 0.1)', fontWeight: '600', color: '#555' }}>Max Activation</td>
                            <td style={{ padding: '14px 16px', borderBottom: '1px solid rgba(156, 43, 109, 0.1)', fontWeight: '700', color: '#9C2B6D', fontSize: '1rem' }}>{results.findings?.max_activation ? (results.findings.max_activation * 100).toFixed(2) : '0.00'}%</td>
                            <td style={{ padding: '14px 16px', borderBottom: '1px solid rgba(156, 43, 109, 0.1)', color: '#666' }}>Peak intensity level detected</td>
                          </tr>
                          <tr style={{ background: 'white' }}>
                            <td style={{ padding: '14px 16px', borderBottom: '1px solid rgba(156, 43, 109, 0.1)', fontWeight: '600', color: '#555' }}>Overall Activity</td>
                            <td style={{ padding: '14px 16px', borderBottom: '1px solid rgba(156, 43, 109, 0.1)', fontWeight: '700', color: '#9C2B6D', fontSize: '1rem' }}>{results.findings?.overall_activation ? (results.findings.overall_activation * 100).toFixed(2) : '0.00'}%</td>
                            <td style={{ padding: '14px 16px', borderBottom: '1px solid rgba(156, 43, 109, 0.1)', color: '#666' }}>Average activation across the image</td>
                          </tr>
                          <tr style={{ background: 'rgba(252, 231, 243, 0.3)' }}>
                            <td style={{ padding: '14px 16px', borderBottom: '1px solid rgba(156, 43, 109, 0.1)', fontWeight: '600', color: '#555' }}>Malignant Probability</td>
                            <td style={{ padding: '14px 16px', borderBottom: '1px solid rgba(156, 43, 109, 0.1)', fontWeight: '700', color: results.malignant > 50 ? '#DC2626' : '#059669', fontSize: '1rem' }}>{results.malignant?.toFixed(2) || '0.00'}%</td>
                            <td style={{ padding: '14px 16px', borderBottom: '1px solid rgba(156, 43, 109, 0.1)', color: '#666' }}>Probability of cancerous tissue</td>
                          </tr>
                          <tr style={{ background: 'white' }}>
                            <td style={{ padding: '14px 16px', borderBottom: 'none', fontWeight: '600', color: '#555', borderBottomLeftRadius: '12px' }}>Benign Probability</td>
                            <td style={{ padding: '14px 16px', borderBottom: 'none', fontWeight: '700', color: results.benign > 50 ? '#059669' : '#DC2626', fontSize: '1rem' }}>{results.benign?.toFixed(2) || '0.00'}%</td>
                            <td style={{ padding: '14px 16px', borderBottom: 'none', color: '#666', borderBottomRightRadius: '12px' }}>Probability of healthy tissue</td>
                          </tr>
                        </tbody>
                      </table>
                    </div>

                    {/* Detected Regions Table */}
                    {results.findings?.regions && results.findings.regions.length > 0 && (
                      <>
                        <h4 className="details-heading" style={{ marginTop: '30px', marginBottom: '15px', fontSize: '1.15rem', color: '#9C2B6D' }}>Detected Regions Detail</h4>
                        <div style={{ overflowX: 'auto', background: 'white', borderRadius: '16px', boxShadow: '0 2px 12px rgba(156, 43, 109, 0.08)', padding: '5px' }}>
                          <table style={{ width: '100%', borderCollapse: 'separate', borderSpacing: '0', fontSize: '0.88rem', marginBottom: '0' }}>
                            <thead>
                              <tr style={{ background: 'linear-gradient(135deg, #fce7f3 0%, #fbcfe8 100%)' }}>
                                <th style={{ padding: '12px 14px', textAlign: 'left', borderBottom: 'none', fontWeight: '700', color: '#9C2B6D', borderTopLeftRadius: '12px' }}>Region</th>
                                <th style={{ padding: '12px 14px', textAlign: 'left', borderBottom: 'none', fontWeight: '700', color: '#9C2B6D' }}>Location</th>
                                <th style={{ padding: '12px 14px', textAlign: 'left', borderBottom: 'none', fontWeight: '700', color: '#9C2B6D' }}>Confidence</th>
                                <th style={{ padding: '12px 14px', textAlign: 'left', borderBottom: 'none', fontWeight: '700', color: '#9C2B6D' }}>Shape</th>
                                <th style={{ padding: '12px 14px', textAlign: 'left', borderBottom: 'none', fontWeight: '700', color: '#9C2B6D' }}>Pattern</th>
                                <th style={{ padding: '12px 14px', textAlign: 'left', borderBottom: 'none', fontWeight: '700', color: '#9C2B6D' }}>Severity</th>
                                <th style={{ padding: '12px 14px', textAlign: 'left', borderBottom: 'none', fontWeight: '700', color: '#9C2B6D', borderTopRightRadius: '12px' }}>Area %</th>
                              </tr>
                            </thead>
                            <tbody>
                              {results.findings.regions.map((region, idx) => (
                                <tr key={idx} style={{ background: idx % 2 === 0 ? 'rgba(252, 231, 243, 0.3)' : 'white' }}>
                                  <td style={{ padding: '12px 14px', borderBottom: idx === results.findings.regions.length - 1 ? 'none' : '1px solid rgba(156, 43, 109, 0.1)', fontWeight: '700', color: '#9C2B6D', fontSize: '0.95rem' }}>#{region.id}</td>
                                  <td style={{ padding: '12px 14px', borderBottom: idx === results.findings.regions.length - 1 ? 'none' : '1px solid rgba(156, 43, 109, 0.1)', color: '#555' }}>{region.location?.quadrant || 'N/A'}</td>
                                  <td style={{ padding: '12px 14px', borderBottom: idx === results.findings.regions.length - 1 ? 'none' : '1px solid rgba(156, 43, 109, 0.1)', fontWeight: '700', color: region.confidence > 70 ? '#DC2626' : region.confidence > 50 ? '#F59E0B' : '#059669', fontSize: '0.95rem' }}>{region.confidence?.toFixed(1)}%</td>
                                  <td style={{ padding: '12px 14px', borderBottom: idx === results.findings.regions.length - 1 ? 'none' : '1px solid rgba(156, 43, 109, 0.1)', color: '#666' }}>{region.shape || 'N/A'}</td>
                                  <td style={{ padding: '12px 14px', borderBottom: idx === results.findings.regions.length - 1 ? 'none' : '1px solid rgba(156, 43, 109, 0.1)', color: '#666' }}>{region.characteristics?.pattern || 'N/A'}</td>
                                  <td style={{ padding: '12px 14px', borderBottom: idx === results.findings.regions.length - 1 ? 'none' : '1px solid rgba(156, 43, 109, 0.1)' }}>
                                    <span style={{
                                      padding: '4px 10px',
                                      borderRadius: '14px',
                                      fontSize: '0.82rem',
                                      fontWeight: '600',
                                      background: region.characteristics?.severity === 'high' ? 'rgba(220, 38, 38, 0.12)' : region.characteristics?.severity === 'moderate' ? 'rgba(245, 158, 11, 0.12)' : 'rgba(16, 185, 129, 0.12)',
                                      color: region.characteristics?.severity === 'high' ? '#DC2626' : region.characteristics?.severity === 'moderate' ? '#F59E0B' : '#059669',
                                      textTransform: 'lowercase'
                                    }}>
                                      {region.characteristics?.severity || 'low'}
                                    </span>
                                  </td>
                                  <td style={{ padding: '12px 14px', borderBottom: idx === results.findings.regions.length - 1 ? 'none' : '1px solid rgba(156, 43, 109, 0.1)', color: '#555', fontWeight: '600' }}>{region.size?.area_percentage?.toFixed(2)}%</td>
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        </div>
                      </>
                    )}

                    {/* No Regions Detected */}
                    {(!results.findings?.regions || results.findings.regions.length === 0) && (
                      <div style={{ padding: '20px', background: 'linear-gradient(135deg, #e5fff5 0%, #f5fffa 100%)', borderRadius: '16px', marginTop: '25px', border: '2px solid #c9ffe5', boxShadow: '0 2px 8px rgba(0,0,0,0.06)' }}>
                        <p style={{ margin: 0, fontSize: '0.95rem', color: '#059669', lineHeight: '1.6' }}>
                          ✓ <strong>No distinct suspicious regions detected.</strong> The tissue appears uniform without focal abnormalities.
                        </p>
                      </div>
                    )}

                  </div>
                )}
                {detailsTab === "nextSteps" && (
                  <div>
                    <h4 className="details-heading">What To Do After Your Results</h4>

                    {results.result?.toLowerCase().includes("malignant") ? (
                      <div>
                        <div style={{ padding: '14px', background: 'rgba(220, 38, 38, 0.08)', borderRadius: '10px', marginBottom: '16px', borderLeft: '4px solid #DC2626' }}>
                          <p style={{ margin: 0, fontWeight: '600', color: '#DC2626' }}>
                            ⚠️ High-Priority Action Required
                          </p>
                        </div>

                        <h4 className="details-heading" style={{ marginTop: '20px' }}>Immediate Steps (Within 1-2 Days)</h4>
                        <ul className="details-list">
                          <li><strong>Contact Your Primary Care Doctor:</strong> Schedule an urgent appointment to discuss these findings.</li>
                          <li><strong>Request Specialist Referral:</strong> Ask for a referral to a breast surgeon or oncologist.</li>
                          <li><strong>Gather Medical History:</strong> Compile your family history of breast cancer and previous mammogram results.</li>
                          <li><strong>Don't Panic:</strong> Remember this is a screening tool. Confirmation requires professional diagnosis.</li>
                        </ul>

                        <h4 className="details-heading" style={{ marginTop: '20px' }}>Follow-Up Diagnostic Tests</h4>
                        <ul className="details-list">
                          <li><strong>Diagnostic Mammogram:</strong> More detailed imaging of suspicious areas</li>
                          <li><strong>Ultrasound:</strong> Helps distinguish between solid masses and fluid-filled cysts</li>
                          <li><strong>MRI (if recommended):</strong> Provides detailed breast tissue images</li>
                          <li><strong>Biopsy:</strong> The only way to definitively diagnose cancer (if abnormalities confirmed)</li>
                        </ul>

                        <h4 className="details-heading" style={{ marginTop: '20px' }}>Questions to Ask Your Doctor</h4>
                        <ul className="details-list">
                          <li>What additional tests do you recommend?</li>
                          <li>How soon should I get these tests done?</li>
                          <li>What are the possible next steps based on test results?</li>
                          <li>Should I consult with a specialist?</li>
                          <li>Are there lifestyle changes I should make immediately?</li>
                        </ul>
                      </div>
                    ) : (
                      <div>
                        <div style={{ padding: '14px', background: 'rgba(16, 185, 129, 0.08)', borderRadius: '10px', marginBottom: '16px', borderLeft: '4px solid #10B981' }}>
                          <p style={{ margin: 0, fontWeight: '600', color: '#059669' }}>
                            ✓ Positive Results - Continue Preventive Care
                          </p>
                        </div>

                        <h4 className="details-heading" style={{ marginTop: '20px' }}>Recommended Actions</h4>
                        <ul className="details-list">
                          <li><strong>Continue Regular Screenings:</strong> Follow age-appropriate screening guidelines (annual or biennial mammograms).</li>
                          <li><strong>Monthly Self-Exams:</strong> Perform breast self-examinations to notice any changes early.</li>
                          <li><strong>Share Results with Doctor:</strong> Discuss these findings at your next routine check-up.</li>
                          <li><strong>Stay Vigilant:</strong> Report any new lumps, changes in breast appearance, or symptoms to your doctor.</li>
                        </ul>

                        <h4 className="details-heading" style={{ marginTop: '20px' }}>Preventive Health Measures</h4>
                        <ul className="details-list">
                          <li><strong>Maintain Healthy Weight:</strong> Obesity increases breast cancer risk</li>
                          <li><strong>Regular Exercise:</strong> Aim for 150+ minutes of moderate activity per week</li>
                          <li><strong>Limit Alcohol:</strong> Reduce alcohol consumption (increases cancer risk)</li>
                          <li><strong>Healthy Diet:</strong> Focus on fruits, vegetables, whole grains</li>
                          <li><strong>Know Your Family History:</strong> Inform your doctor if there's a family history of breast cancer</li>
                        </ul>

                        <h4 className="details-heading" style={{ marginTop: '20px' }}>When to Seek Immediate Medical Attention</h4>
                        <ul className="details-list">
                          <li>New lump or thickening in breast or underarm</li>
                          <li>Change in breast size, shape, or contour</li>
                          <li>Dimpling, puckering, or redness of breast skin</li>
                          <li>Nipple discharge, retraction, or changes</li>
                          <li>Persistent breast or nipple pain</li>
                        </ul>
                      </div>
                    )}

                    <div style={{ marginTop: '20px', padding: '14px', background: 'rgba(192, 37, 108, 0.08)', borderRadius: '10px' }}>
                      <p style={{ margin: 0, fontSize: '0.95rem', lineHeight: '1.7' }}>
                        <strong>Remember:</strong> This AI analysis is a supplementary screening tool. All findings should be
                        reviewed and confirmed by qualified healthcare professionals. When in doubt, always consult your doctor.
                      </p>
                    </div>
                  </div>
                )}
              </div>
            </section>

            <div className="btn-row" style={{ flexDirection: "column", gap: "16px" }}>
              <button
                className="btn-primary"
                onClick={handleDownloadReport}
                disabled={isGeneratingReport}
              >
                {isGeneratingReport ? "Preparing Report…" : "Download PDF Report"}
              </button>
              <button className="btn-secondary" onClick={handleBackToUpload}>
                Analyze Another Image
              </button>
            </div>

          </section>
        </main>
      )}
    </div>
  );
}

export default AppContent;

