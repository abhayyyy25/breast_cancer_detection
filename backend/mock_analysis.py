"""
Mock AI Analysis Module

Provides fallback analysis when TensorFlow is not available.
Generates demo predictions for testing purposes.

⚠️ FOR DEVELOPMENT/DEMO ONLY - NOT FOR PRODUCTION USE
"""

import random
import numpy as np
from PIL import Image
import base64
import io
from typing import Dict, Any, Tuple


def calculate_image_statistics(image: Image.Image) -> Dict[str, float]:
    """
    Calculate basic image statistics.
    
    Args:
        image: PIL Image object
    
    Returns:
        Dictionary with image statistics
    """
    # Convert to numpy array
    img_array = np.array(image)
    
    # Calculate statistics
    mean_intensity = float(np.mean(img_array))
    std_intensity = float(np.std(img_array))
    
    # Calculate brightness (0-255 scale)
    brightness = mean_intensity
    
    # Calculate contrast (higher std = more contrast)
    contrast = std_intensity
    
    return {
        "mean_intensity": round(mean_intensity, 2),
        "std_intensity": round(std_intensity, 2),
        "brightness": round(brightness, 2),
        "contrast": round(contrast, 2)
    }


def generate_mock_prediction(image: Image.Image, use_seed: bool = False) -> Dict[str, Any]:
    """
    Generate a mock AI prediction for demonstration purposes.
    
    Uses image characteristics to generate semi-realistic predictions.
    
    Args:
        image: PIL Image object to analyze
        use_seed: If True, uses image hash as seed for reproducible results
    
    Returns:
        Dictionary with prediction results
    """
    # Use image properties to seed random generator for consistency
    if use_seed:
        img_hash = hash(image.tobytes())
        random.seed(img_hash % 10000)
    
    # Generate base probabilities
    # Most breast scans are benign (realistic distribution)
    benign_prob = random.uniform(0.60, 0.95)
    malignant_prob = 1.0 - benign_prob
    
    # Determine result
    if malignant_prob > 0.5:
        result = "Malignant"
        confidence = malignant_prob
    else:
        result = "Benign"
        confidence = benign_prob
    
    # Determine risk level
    if malignant_prob >= 0.70:
        risk_level = "🔴 Very High Risk"
        risk_icon = "🔴"
    elif malignant_prob >= 0.50:
        risk_level = "🟠 High Risk"
        risk_icon = "🟠"
    elif malignant_prob >= 0.30:
        risk_level = "🟡 Moderate Risk"
        risk_icon = "🟡"
    else:
        risk_level = "🟢 Low Risk"
        risk_icon = "🟢"
    
    # Calculate image statistics
    stats = calculate_image_statistics(image)
    
    # Generate mock findings
    findings = {
        "mass_detected": malignant_prob > 0.40,
        "calcifications": malignant_prob > 0.50,
        "architectural_distortion": malignant_prob > 0.60,
        "asymmetry": random.choice([True, False])
    }
    
    return {
        "result": result,
        "confidence": round(confidence * 100, 1),
        "malignant_prob": round(malignant_prob * 100, 1),
        "benign_prob": round(benign_prob * 100, 1),
        "risk_level": risk_level,
        "risk_icon": risk_icon,
        "stats": stats,
        "image_size": {
            "width": image.width,
            "height": image.height
        },
        "file_format": image.format or "Unknown",
        "findings": findings,
        "mode": "DEMO"  # Indicator that this is demo mode
    }


def create_mock_heatmap(image: Image.Image) -> Image.Image:
    """
    Create a simple mock heatmap overlay.
    
    Args:
        image: Original PIL Image
    
    Returns:
        PIL Image with mock heatmap overlay
    """
    # Create a copy
    overlay = image.copy().convert("RGBA")
    
    # Create a semi-transparent red overlay in center
    width, height = overlay.size
    center_x, center_y = width // 2, height // 2
    
    # Create gradient effect
    for y in range(height):
        for x in range(width):
            # Calculate distance from center
            dx = x - center_x
            dy = y - center_y
            distance = np.sqrt(dx*dx + dy*dy)
            max_distance = np.sqrt(center_x*center_x + center_y*center_y)
            
            # Create radial gradient (stronger in center)
            intensity = max(0, 1 - (distance / max_distance))
            
            if intensity > 0.3:  # Only show in central region
                alpha = int(intensity * 100)  # Semi-transparent
                red_overlay = Image.new('RGBA', (1, 1), (255, 0, 0, alpha))
                overlay.paste(red_overlay, (x, y), red_overlay)
    
    return overlay


def pil_to_base64(image: Image.Image, format: str = "PNG") -> str:
    """
    Convert PIL Image to base64 string.
    
    Args:
        image: PIL Image object
        format: Image format (PNG, JPEG, etc.)
    
    Returns:
        Base64 encoded string
    """
    buffered = io.BytesIO()
    
    # Convert RGBA to RGB if saving as JPEG
    if format.upper() == "JPEG" and image.mode == "RGBA":
        # Create white background
        rgb_image = Image.new("RGB", image.size, (255, 255, 255))
        rgb_image.paste(image, mask=image.split()[3] if len(image.split()) == 4 else None)
        rgb_image.save(buffered, format=format, quality=95)
    else:
        image.save(buffered, format=format)
    
    img_str = base64.b64encode(buffered.getvalue()).decode()
    return f"data:image/{format.lower()};base64,{img_str}"


def run_mock_analysis(image: Image.Image) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """
    Run complete mock analysis on an image.
    
    Args:
        image: PIL Image object
    
    Returns:
        Tuple of (analysis_results, image_data)
    """
    # Ensure RGB mode
    if image.mode != "RGB":
        image = image.convert("RGB")
    
    # Generate prediction
    analysis = generate_mock_prediction(image, use_seed=True)
    
    # Create mock heatmap
    try:
        heatmap = create_mock_heatmap(image)
        heatmap_b64 = pil_to_base64(heatmap, "PNG")
    except Exception:
        heatmap_b64 = pil_to_base64(image, "PNG")
    
    # Convert original to base64
    original_b64 = pil_to_base64(image, "JPEG")
    
    # Prepare image data
    images = {
        "original_base64": original_b64,
        "heatmap_base64": heatmap_b64,
        "overlay_base64": heatmap_b64,  # Same as heatmap for simplicity
        "bbox_base64": None  # Not implemented in mock
    }
    
    return analysis, images


# Demo mode indicator
DEMO_MODE = True
DEMO_MESSAGE = "⚠️ DEMO MODE: Using simulated AI predictions. Install TensorFlow for real analysis."

