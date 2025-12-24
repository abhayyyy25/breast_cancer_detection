# def main():
#     print("Hello from repl-nix-workspace!")


# if __name__ == "__main__":
#     main()


# main.py  -> FastAPI backend

from fastapi import FastAPI, UploadFile, File, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from typing import Dict, Any, Tuple, Optional, List
from contextlib import asynccontextmanager

import base64
import io
import os
from pathlib import Path

import numpy as np
from PIL import Image

# Make TensorFlow optional - system will work without AI analysis
try:
    from tensorflow import keras
    TENSORFLOW_AVAILABLE = True
except Exception as e:
    TENSORFLOW_AVAILABLE = False
    print(f"WARNING: TensorFlow not available - AI analysis will be disabled. Error: {e}")

try:
    from grad_cam import create_gradcam_visualization
    from report_generator import generate_report_pdf
    ANALYSIS_AVAILABLE = True
except Exception as e:
    ANALYSIS_AVAILABLE = False
    print(f"WARNING: Analysis modules not available. Error: {e}")

# Import database and auth
from database import init_db, get_db
from models import User
from auth_utils import get_current_user, get_current_active_doctor

# Import routers
from routers import auth, patients, scans


# Lifespan context manager for startup/shutdown events
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize database
    print("=" * 80)
    print("Starting Breast Cancer Detection Hospital System...")
    print("=" * 80)
    
    # Import models to ensure they're registered with Base
    from models import User, Patient, Scan
    
    # Get database URL for logging
    db_url = os.environ.get("DATABASE_URL", "sqlite:///./breast_cancer_detection.db")
    db_type = "PostgreSQL" if db_url.startswith("postgresql") else "SQLite"
    print(f"[*] Database: {db_type}")
    print(f"[*] Database URL: {db_url[:50]}...")  # Show first 50 chars for security
    
    # Initialize database
    try:
        init_db()
        print("[OK] Database initialized successfully")
    except Exception as e:
        print(f"[ERROR] Failed to initialize database: {e}")
        raise
    
    print("=" * 80)
    yield
    # Shutdown: Cleanup if needed
    print("=" * 80)
    print("Shutting down...")
    print("=" * 80)


app = FastAPI(
    title="Breast Cancer Detection Hospital System API",
    description=(
        "Enterprise-Level AI-based Breast Cancer Detection System.\n"
        "Secure authentication, patient management, and AI-powered diagnosis.\n\n"
        "⚠ AI-ASSISTED DIAGNOSIS – NOT A REPLACEMENT FOR MEDICAL JUDGMENT.\n"
        "This system complies with HIPAA/GDPR requirements for audit logging."
    ),
    version="2.0.0",
    lifespan=lifespan
)

# Include routers
app.include_router(auth.router)
app.include_router(patients.router)
app.include_router(scans.router)

# ----------------- MODEL LOADING (shared) -----------------
BASE_DIR = Path(__file__).resolve().parent
MODEL_PATH = Path(os.environ.get("MODEL_PATH", BASE_DIR / "models" / "breast_cancer_model.keras"))
_model: Optional[Any] = None  # Changed from keras.Model to Any for compatibility


def get_model():
    """Model sirf ek baar load karo, baar-baar reuse karein."""
    if not TENSORFLOW_AVAILABLE:
        raise RuntimeError("TensorFlow is not available. Please install: pip install tensorflow-cpu")
    
    global _model
    if _model is None:
        if not MODEL_PATH.exists():
            raise RuntimeError(f"Model file not found at {MODEL_PATH}. Set MODEL_PATH env var if stored elsewhere.")
        try:
            # Try loading with safe_mode=False for compatibility
            _model = keras.models.load_model(MODEL_PATH, compile=False, safe_mode=False)
            _model.compile(optimizer='adam', loss='binary_crossentropy', metrics=['accuracy'])
        except TypeError as e:
            if "batch_shape" in str(e) or "safe_mode" in str(e):
                # Keras version mismatch - recreate the model architecture
                print("Keras version mismatch detected, rebuilding model...")
                _model = _create_compatible_model()
                _load_weights_from_keras_file(_model, MODEL_PATH)
            else:
                raise e
    return _model


def _create_compatible_model():
    """Create a compatible model architecture for breast cancer detection."""
    from tensorflow.keras import layers, Sequential
    
    model = Sequential([
        layers.Input(shape=(224, 224, 3)),
        layers.Conv2D(32, (3, 3), activation='relu'),
        layers.MaxPooling2D((2, 2)),
        layers.Conv2D(64, (3, 3), activation='relu'),
        layers.MaxPooling2D((2, 2)),
        layers.Conv2D(128, (3, 3), activation='relu'),
        layers.MaxPooling2D((2, 2)),
        layers.Conv2D(128, (3, 3), activation='relu'),
        layers.MaxPooling2D((2, 2)),
        layers.Flatten(),
        layers.Dense(512, activation='relu'),
        layers.Dropout(0.5),
        layers.Dense(1, activation='sigmoid')
    ])
    
    model.compile(
        optimizer='adam',
        loss='binary_crossentropy',
        metrics=['accuracy']
    )
    
    return model


def _load_weights_from_keras_file(model, keras_path: Path):
    """Extract and load weights from a .keras file."""
    import zipfile
    import tempfile
    import shutil
    
    try:
        temp_dir = tempfile.mkdtemp()
        with zipfile.ZipFile(keras_path, 'r') as zip_ref:
            zip_ref.extractall(temp_dir)
        
        weights_path = os.path.join(temp_dir, "model.weights.h5")
        if os.path.exists(weights_path):
            model.load_weights(weights_path)
            print("Weights loaded successfully!")
        else:
            print("No weights file found, using random initialization")
        
        shutil.rmtree(temp_dir)
    except Exception as e:
        print(f"Could not load weights: {e}")


# ----------------- HELPERS: preprocessing, stats, risk -----------------

def preprocess_image(image: Image.Image) -> np.ndarray:
    """Streamlit code se hi liya hai: resize 224x224, normalize, RGB fix."""
    img = image.resize((224, 224), Image.LANCZOS)
    img_array = np.array(img)

    if img_array.ndim == 2:  # grayscale
        img_array = np.stack([img_array] * 3, axis=-1)
    elif img_array.shape[2] == 4:  # RGBA
        img_array = img_array[:, :, :3]

    img_array = img_array.astype("float32") / 255.0
    img_array = np.expand_dims(img_array, axis=0)
    return img_array


def get_image_statistics(image: Image.Image) -> Dict[str, float]:
    img_array = np.array(image)

    if img_array.ndim == 2:
        img_array = np.stack([img_array] * 3, axis=-1)
    elif img_array.shape[2] == 4:
        img_array = img_array[:, :, :3]

    stats = {
        "mean_intensity": float(np.mean(img_array)),
        "std_intensity": float(np.std(img_array)),
        "min_intensity": float(np.min(img_array)),
        "max_intensity": float(np.max(img_array)),
        "median_intensity": float(np.median(img_array)),
        "brightness": float(np.mean(img_array) / 255.0 * 100),
        "contrast": float(np.std(img_array) / 255.0 * 100),
    }
    return stats


def get_risk_level(confidence: float) -> Tuple[str, str, str]:
    """
    Tumhare Streamlit wale get_risk_level se same logic.
    confidence = P(malignant)
    """
    if confidence > 0.5:
        malignant_prob = confidence * 100
        if malignant_prob >= 90:
            return "Very High Risk", "🔴", "#ff0000"
        elif malignant_prob >= 75:
            return "High Risk", "🟠", "#ff6600"
        elif malignant_prob >= 60:
            return "Moderate-High Risk", "🟡", "#ffaa00"
        else:
            return "Moderate Risk", "🟡", "#ffcc00"
    else:
        benign_prob = (1 - confidence) * 100
        if benign_prob >= 90:
            return "Very Low Risk", "🟢", "#00cc00"
        elif benign_prob >= 75:
            return "Low Risk", "🟢", "#33cc33"
        elif benign_prob >= 60:
            return "Low-Moderate Risk", "🟡", "#99cc00"
        else:
            return "Moderate Risk", "🟡", "#cccc00"


def pil_to_base64(image: Optional[Image.Image]) -> Optional[str]:
    if image is None:
        return None
    buf = io.BytesIO()
    image.save(buf, format="PNG")
    buf.seek(0)
    return base64.b64encode(buf.read()).decode("utf-8")


# ----------------- CORE ANALYSIS LOGIC (Streamlit ka brain yahan) -----------------

def run_full_analysis(image: Image.Image) -> Tuple[Dict[str, Any], Dict[str, Image.Image]]:
    """
    Yeh function tumhari Streamlit logic ka backend version hai:
    - model se prediction
    - stats
    - Grad-CAM heatmaps
    - risk level, probabilities
    - detailed findings from image analysis
    """
    model = get_model()
    preprocessed = preprocess_image(image)

    # model.predict -> sigmoid output
    prediction = float(model.predict(preprocessed, verbose=0)[0][0])
    confidence = prediction

    stats = get_image_statistics(image)

    benign_prob = (1 - confidence) * 100
    malignant_prob = confidence * 100

    (
        heatmap_array,
        overlay_image,
        heatmap_only,
        bbox_image,
        heatmap_error,
        detailed_findings,
    ) = create_gradcam_visualization(image, preprocessed, model, confidence)

    if confidence > 0.5:
        result = "Malignant (Cancerous)"
        probability = malignant_prob
    else:
        result = "Benign (Non-Cancerous)"
        probability = benign_prob

    # risk level (same logic as app.py)
    if malignant_prob > 90:
        risk_level = "Very High Risk"
    elif malignant_prob > 75:
        risk_level = "High Risk"
    elif malignant_prob > 60:
        risk_level = "Moderate-High Risk"
    elif malignant_prob > 40:
        risk_level = "Moderate Risk"
    elif malignant_prob > 25:
        risk_level = "Low-Moderate Risk"
    elif malignant_prob > 10:
        risk_level = "Low Risk"
    else:
        risk_level = "Very Low Risk"

    risk_level2, risk_icon, risk_color = get_risk_level(confidence)

    analysis: Dict[str, Any] = {
        "result": result,
        "probability": float(probability),
        "confidence": float(confidence),
        "benign_prob": float(benign_prob),
        "malignant_prob": float(malignant_prob),
        "risk_level": risk_level,
        "risk_icon": risk_icon,
        "risk_color": risk_color,
        "stats": stats,
        "heatmap_error": heatmap_error,
        "image_size": {"width": image.size[0], "height": image.size[1]},
        "file_format": image.format or "N/A",
        "findings": detailed_findings,  # NEW: Detailed findings from the image
    }

    images = {
        "original": image,
        "overlay_image": overlay_image,
        "heatmap_only": heatmap_only,
        "bbox_image": bbox_image,
    }

    return analysis, images


# ----------------- CORS (React ke liye) -----------------
def _parse_origins(env_value: str) -> List[str]:
    if not env_value or env_value.strip() == "*":
        return ["*"]
    return [origin.strip() for origin in env_value.split(",") if origin.strip()]


ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:3001",
    "http://localhost:8001",
    "http://127.0.0.1:8001"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]
)


# ----------------- ROUTES -----------------

@app.get("/")
async def root():
    """Root endpoint with API info."""
    return {
        "message": "Breast Cancer Detection Hospital System API",
        "version": "2.0.0",
        "status": "running",
        "tensorflow_available": TENSORFLOW_AVAILABLE,
        "endpoints": {
            "health": "/health",
            "auth": "/auth/* (authentication)",
            "patients": "/patients/* (patient management)",
            "scans": "/scans/* (scan analysis)",
            "docs": "/docs (API documentation)"
        }
    }


@app.get("/health")
async def health_check():
    """Simple health check - returns ok if server is running."""
    return {
        "status": "healthy",
        "environment": "development",
        "tensorflow_available": TENSORFLOW_AVAILABLE,
        "analysis_available": ANALYSIS_AVAILABLE
    }


@app.post("/analyze")
async def analyze_image(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_doctor)
):
    """
    Analyze medical image (LEGACY ENDPOINT - Use /scans/analyze instead).
    
    ⚠️ DEPRECATED: This endpoint is kept for backward compatibility.
    Please use POST /scans/analyze with patient_id for new implementations.
    
    - Requires doctor authentication
    - Analyzes image with AI model
    - Returns prediction results
    
    ⚠️ This is AI-assisted diagnosis, not a replacement for medical judgment.
    """
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Please upload an image file.")

    data = await file.read()
    try:
        image = Image.open(io.BytesIO(data)).convert("RGB")
    except Exception:
        raise HTTPException(status_code=400, detail="Unable to read image file.")

    try:
        analysis, images = run_full_analysis(image)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {exc}")

    return {
        **analysis,
        "stats": {k: float(v) for k, v in analysis["stats"].items()},
        "images": {
            "original": pil_to_base64(images["original"]),
            "overlay": pil_to_base64(images["overlay_image"]),
            "heatmap_only": pil_to_base64(images["heatmap_only"]),
            "bbox": pil_to_base64(images["bbox_image"]),
        },
    }


@app.post("/report")
async def generate_report(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_doctor)
):
    """
    Generate PDF report from image (LEGACY ENDPOINT - Use /scans/{id}/download-report instead).
    
    ⚠️ DEPRECATED: This endpoint is kept for backward compatibility.
    Please use GET /scans/{scan_id}/download-report for new implementations.
    
    - Requires doctor authentication
    - Analyzes image and generates PDF report
    
    ⚠️ This is AI-assisted diagnosis, not a replacement for medical judgment.
    """
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Please upload an image file.")

    data = await file.read()
    try:
        image = Image.open(io.BytesIO(data)).convert("RGB")
    except Exception:
        raise HTTPException(status_code=400, detail="Unable to read image file.")

    try:
        analysis, images = run_full_analysis(image)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {exc}")

    pdf_bytes = generate_report_pdf(
        result=analysis["result"],
        probability=analysis["probability"],
        risk_level=analysis["risk_level"],
        benign_prob=analysis["benign_prob"],
        malignant_prob=analysis["malignant_prob"],
        stats=analysis["stats"],
        image_size=(analysis["image_size"]["width"], analysis["image_size"]["height"]),
        file_format=analysis["file_format"],
        original_image=images["original"],
        overlay_image=images["overlay_image"],
        heatmap_only=images["heatmap_only"],
        bbox_image=images["bbox_image"],
        confidence=analysis["confidence"],
    )

    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": 'attachment; filename="breast_cancer_report.pdf"'},
    )

# Run command:
# uvicorn main:app --reload --port 8000
