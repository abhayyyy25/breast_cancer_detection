import tensorflow as tf
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import matplotlib

matplotlib.use("Agg")  # Ensure headless rendering for serverless environments
import matplotlib.cm as cm
import matplotlib.pyplot as plt
from scipy import ndimage

def make_gradcam_heatmap(img_array, model, last_conv_layer_index, pred_index=None):
    """
    Generate Grad-CAM heatmap for a given image and model.
    
    Args:
        img_array: Preprocessed input image (batch_size, height, width, channels)
        model: The trained model  
        last_conv_layer_index: Index of the last convolutional layer
        pred_index: Index of the class to visualize (None for top prediction)
    
    Returns:
        Normalized heatmap as numpy array
    """
    # Get the last convolutional layer
    last_conv_layer = model.layers[last_conv_layer_index]
    
    # For loaded Sequential models, we need to create inputs manually
    # Create a new input tensor
    inputs = tf.keras.Input(shape=(224, 224, 3))
    
    # Pass through all layers up to and including the last conv layer
    x = inputs
    for i, layer in enumerate(model.layers):
        x = layer(x)
        if i == last_conv_layer_index:
            conv_output = x
    
    # Get the final output
    final_output = x
    
    # Create a model that maps inputs to activations of the last conv layer and the output predictions
    grad_model = tf.keras.Model(
        inputs=inputs,
        outputs=[conv_output, final_output]
    )
    
    with tf.GradientTape() as tape:
        conv_outputs, predictions = grad_model(img_array)
        if pred_index is None:
            pred_index = 0
        class_channel = predictions[:, pred_index]
    
    grads = tape.gradient(class_channel, conv_outputs)
    
    if grads is None:
        return None
    
    pooled_grads = tf.reduce_mean(grads, axis=(0, 1, 2))
    
    conv_outputs = conv_outputs[0]
    heatmap = conv_outputs @ pooled_grads[..., tf.newaxis]
    heatmap = tf.squeeze(heatmap)
    
    heatmap = tf.maximum(heatmap, 0)
    max_val = tf.math.reduce_max(heatmap)
    if max_val > 0:
        heatmap = heatmap / max_val
    
    return heatmap.numpy()

def create_tissue_mask(img_array, threshold=15):
    """
    Create a mask identifying tissue (non-background) areas.
    
    Args:
        img_array: Image as numpy array
        threshold: Pixel intensity threshold to distinguish tissue from background
    
    Returns:
        Binary mask where True = tissue area
    """
    if len(img_array.shape) == 3:
        gray = np.mean(img_array, axis=2)
    else:
        gray = img_array
    
    # Tissue is where pixel intensity is above threshold (not black background)
    mask = gray > threshold
    return mask


def create_intensity_based_heatmap(img_array):
    """Create heatmap based on image intensity - highlights bright regions (potential lesions)."""
    from scipy.ndimage import gaussian_filter
    
    if len(img_array.shape) == 3:
        gray = np.mean(img_array, axis=2)
    else:
        gray = img_array.copy()
    
    # Normalize
    gray = gray.astype(np.float32)
    g_min, g_max = np.min(gray), np.max(gray)
    if g_max > g_min:
        gray = (gray - g_min) / (g_max - g_min)
    
    # Apply Gaussian blur to smooth
    gray = gaussian_filter(gray, sigma=3)
    
    # Enhance contrast - focus on bright regions
    gray = np.power(gray, 0.7)
    
    # Normalize again
    g_min, g_max = np.min(gray), np.max(gray)
    if g_max > g_min:
        gray = (gray - g_min) / (g_max - g_min)
    
    return gray


def create_heatmap_overlay(original_image, heatmap, alpha=0.5, colormap='jet'):
    """
    Create an overlay of the heatmap on the original image.
    Only shows heatmap on tissue areas, not on black background.
    Uses intensity-based fallback if Grad-CAM fails.
    
    Args:
        original_image: PIL Image object
        heatmap: Normalized heatmap array
        alpha: Transparency of the heatmap overlay (0-1)
        colormap: Matplotlib colormap name
    
    Returns:
        PIL Image with heatmap overlay
    """
    img_array = np.array(original_image)
    
    # Check if Grad-CAM heatmap has meaningful variation
    hmap_range = np.max(heatmap) - np.min(heatmap)
    print(f"DEBUG: Heatmap range = {hmap_range:.4f}")
    
    if hmap_range < 0.01:
        # Grad-CAM failed - use intensity-based heatmap as fallback
        print("DEBUG: Grad-CAM heatmap has no variation, using intensity-based fallback")
        img_small = np.array(original_image.resize((heatmap.shape[1], heatmap.shape[0])))
        heatmap = create_intensity_based_heatmap(img_small)
    
    # Enhance contrast
    hmap_min, hmap_max = np.min(heatmap), np.max(heatmap)
    if hmap_max > hmap_min:
        heatmap = (heatmap - hmap_min) / (hmap_max - hmap_min)
    
    # Apply gamma for better visibility
    heatmap = np.power(heatmap, 0.5)
    
    heatmap_resized = np.array(Image.fromarray((heatmap * 255).astype(np.uint8)).resize(
        (original_image.size[0], original_image.size[1]),
        Image.BILINEAR
    ))
    
    heatmap_resized = heatmap_resized.astype(np.float32) / 255.0
    
    # Create tissue mask to avoid showing heatmap on black background
    tissue_mask = create_tissue_mask(img_array, threshold=15)
    
    # Zero out heatmap in background areas
    heatmap_resized = heatmap_resized * tissue_mask
    
    cmap = cm.get_cmap(colormap)
    heatmap_colored = cmap(heatmap_resized)
    heatmap_colored = (heatmap_colored[:, :, :3] * 255).astype(np.uint8)
    
    if len(img_array.shape) == 2:
        img_array = np.stack([img_array] * 3, axis=-1)
    elif img_array.shape[2] == 4:
        img_array = img_array[:, :, :3]
    
    # Only apply overlay where there is tissue
    overlay = img_array.copy().astype(np.float32)
    tissue_mask_3d = np.stack([tissue_mask] * 3, axis=-1)
    overlay = np.where(tissue_mask_3d, 
                       (1 - alpha) * img_array + alpha * heatmap_colored,
                       img_array)
    overlay = np.clip(overlay, 0, 255).astype(np.uint8)
    
    return Image.fromarray(overlay)

def get_last_conv_layer_index(model):
    """
    Find the index of the last convolutional layer in the model.
    
    Args:
        model: Keras model
    
    Returns:
        Index of the last Conv2D layer
    """
    conv_layer_indices = [i for i, layer in enumerate(model.layers) if isinstance(layer, tf.keras.layers.Conv2D)]
    if conv_layer_indices:
        return conv_layer_indices[-1]
    return None

def detect_bounding_boxes(heatmap, original_image_size, threshold=0.6, min_area=100, tissue_mask=None):
    """
    Detect bounding boxes around high-activation regions in the heatmap.
    Only detects within tissue areas if tissue_mask is provided.
    
    Args:
        heatmap: Normalized heatmap array (values 0-1)
        original_image_size: Tuple of (width, height) of original image
        threshold: Activation threshold (0-1) for detecting regions
        min_area: Minimum area in pixels for a region to be considered
        tissue_mask: Optional binary mask of tissue area (same size as original image)
    
    Returns:
        List of bounding boxes [(x1, y1, x2, y2, confidence), ...]
    """
    # If tissue mask provided, resize it to heatmap size and apply
    if tissue_mask is not None:
        # Resize tissue mask to heatmap dimensions
        tissue_mask_resized = np.array(Image.fromarray(tissue_mask.astype(np.uint8) * 255).resize(
            (heatmap.shape[1], heatmap.shape[0]),
            Image.NEAREST
        )) > 127
        # Zero out heatmap in background areas
        heatmap = heatmap * tissue_mask_resized
    
    # Threshold the heatmap to get high-activation regions
    binary_mask = (heatmap > threshold).astype(np.uint8)
    
    # Label connected components
    labeled_array, num_features = ndimage.label(binary_mask)
    
    boxes = []
    heatmap_h, heatmap_w = heatmap.shape
    orig_w, orig_h = original_image_size
    
    scale_x = orig_w / heatmap_w
    scale_y = orig_h / heatmap_h
    
    for region_id in range(1, num_features + 1):
        # Get coordinates of this region
        region_coords = np.where(labeled_array == region_id)
        
        if len(region_coords[0]) < min_area / (scale_x * scale_y):
            continue
        
        # Get bounding box coordinates in heatmap space
        y_min, y_max = region_coords[0].min(), region_coords[0].max()
        x_min, x_max = region_coords[1].min(), region_coords[1].max()
        
        # Scale to original image size
        x1 = int(x_min * scale_x)
        y1 = int(y_min * scale_y)
        x2 = int(x_max * scale_x)
        y2 = int(y_max * scale_y)
        
        # Calculate confidence (average activation in this region)
        region_mask = (labeled_array == region_id)
        confidence = float(heatmap[region_mask].mean())
        
        boxes.append((x1, y1, x2, y2, confidence))
    
    return boxes

def draw_bounding_boxes(image, boxes, box_color='red', text_color='white', line_width=3):
    """
    Draw bounding boxes on an image.
    
    Args:
        image: PIL Image
        boxes: List of bounding boxes [(x1, y1, x2, y2, confidence), ...]
        box_color: Color for the bounding box
        text_color: Color for the confidence text
        line_width: Width of the bounding box lines
    
    Returns:
        PIL Image with bounding boxes drawn
    """
    img_copy = image.copy()
    draw = ImageDraw.Draw(img_copy)
    
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 16)
    except:
        font = ImageFont.load_default()
    
    for i, (x1, y1, x2, y2, confidence) in enumerate(boxes):
        # Draw rectangle
        draw.rectangle([x1, y1, x2, y2], outline=box_color, width=line_width)
        
        # Draw label - position above or inside box depending on space
        label = f"Region {i+1}: {confidence*100:.1f}%"
        
        # Check if there's enough space above the box (need ~25 pixels)
        if y1 >= 25:
            label_y = y1 - 20
        else:
            # Not enough space above, put it inside the box at the top
            label_y = y1 + 5
        
        bbox = draw.textbbox((x1, label_y), label, font=font)
        draw.rectangle([bbox[0]-2, bbox[1]-2, bbox[2]+2, bbox[3]+2], fill=box_color)
        
        # Draw label text
        draw.text((x1, label_y), label, fill=text_color, font=font)
    
    return img_copy

def get_region_location(x1, y1, x2, y2, img_width, img_height):
    """
    Determine the anatomical location of a detected region.
    """
    center_x = (x1 + x2) / 2
    center_y = (y1 + y2) / 2
    
    # Determine horizontal position
    if center_x < img_width * 0.33:
        h_pos = "lateral"
    elif center_x > img_width * 0.67:
        h_pos = "medial"
    else:
        h_pos = "central"
    
    # Determine vertical position
    if center_y < img_height * 0.33:
        v_pos = "upper"
    elif center_y > img_height * 0.67:
        v_pos = "lower"
    else:
        v_pos = "mid"
    
    # Quadrant determination
    if center_x < img_width * 0.5 and center_y < img_height * 0.5:
        quadrant = "upper-outer quadrant"
    elif center_x >= img_width * 0.5 and center_y < img_height * 0.5:
        quadrant = "upper-inner quadrant"
    elif center_x < img_width * 0.5 and center_y >= img_height * 0.5:
        quadrant = "lower-outer quadrant"
    else:
        quadrant = "lower-inner quadrant"
    
    return {
        "position": f"{v_pos}-{h_pos}",
        "quadrant": quadrant,
        "description": f"{v_pos} {h_pos} region ({quadrant})"
    }


def analyze_region_characteristics(heatmap, x1, y1, x2, y2, scale_x, scale_y):
    """
    Analyze characteristics of a detected region.
    """
    # Convert to heatmap coordinates
    hx1, hy1 = int(x1 / scale_x), int(y1 / scale_y)
    hx2, hy2 = int(x2 / scale_x), int(y2 / scale_y)
    
    # Ensure bounds
    hx1, hx2 = max(0, hx1), min(heatmap.shape[1], hx2)
    hy1, hy2 = max(0, hy1), min(heatmap.shape[0], hy2)
    
    region = heatmap[hy1:hy2, hx1:hx2]
    
    if region.size == 0:
        return {}
    
    # Calculate characteristics
    mean_intensity = float(np.mean(region))
    max_intensity = float(np.max(region))
    std_intensity = float(np.std(region))
    
    # Determine pattern type based on intensity distribution
    if std_intensity < 0.1:
        pattern = "homogeneous"
    elif std_intensity < 0.2:
        pattern = "slightly heterogeneous"
    else:
        pattern = "heterogeneous"
    
    # Determine severity
    if max_intensity > 0.9:
        severity = "high"
    elif max_intensity > 0.7:
        severity = "moderate"
    else:
        severity = "low"
    
    return {
        "mean_intensity": mean_intensity,
        "max_intensity": max_intensity,
        "pattern": pattern,
        "severity": severity
    }


def extract_detailed_findings(heatmap, boxes, original_image_size, confidence):
    """
    Extract detailed findings from the heatmap analysis.
    """
    img_width, img_height = original_image_size
    heatmap_h, heatmap_w = heatmap.shape
    scale_x = img_width / heatmap_w
    scale_y = img_height / heatmap_h
    
    findings = {
        "num_regions": len(boxes),
        "overall_activation": float(np.mean(heatmap)),
        "max_activation": float(np.max(heatmap)),
        "high_attention_percentage": float(np.sum(heatmap > 0.5) / heatmap.size * 100),
        "regions": [],
        "summary": ""
    }
    
    for i, (x1, y1, x2, y2, conf) in enumerate(boxes):
        # Calculate region size
        width_px = x2 - x1
        height_px = y2 - y1
        area_px = width_px * height_px
        area_percentage = (area_px / (img_width * img_height)) * 100
        
        # Get location
        location = get_region_location(x1, y1, x2, y2, img_width, img_height)
        
        # Get characteristics
        characteristics = analyze_region_characteristics(heatmap, x1, y1, x2, y2, scale_x, scale_y)
        
        # Determine shape based on aspect ratio
        aspect_ratio = width_px / height_px if height_px > 0 else 1
        if 0.8 <= aspect_ratio <= 1.2:
            shape = "roughly circular"
        elif aspect_ratio > 1.2:
            shape = "horizontally elongated"
        else:
            shape = "vertically elongated"
        
        region_info = {
            "id": i + 1,
            "confidence": float(conf * 100),
            "location": location,
            "size": {
                "width_px": width_px,
                "height_px": height_px,
                "area_percentage": round(area_percentage, 2)
            },
            "shape": shape,
            "characteristics": characteristics,
            "bbox": {"x1": x1, "y1": y1, "x2": x2, "y2": y2}
        }
        findings["regions"].append(region_info)
    
    # Generate summary
    if len(boxes) == 0:
        if confidence > 0.5:
            findings["summary"] = "Diffuse abnormal patterns detected across the tissue without distinct focal masses."
        else:
            findings["summary"] = "No distinct suspicious regions identified. Tissue appears uniform and normal."
    elif len(boxes) == 1:
        r = findings["regions"][0]
        findings["summary"] = f"Single suspicious region detected in the {r['location']['description']} with {r['confidence']:.1f}% confidence. The lesion appears {r['shape']} and shows {r['characteristics'].get('pattern', 'undefined')} density pattern."
    else:
        locations = [r['location']['quadrant'] for r in findings['regions']]
        findings["summary"] = f"Multiple suspicious regions ({len(boxes)}) detected across {', '.join(set(locations))}. This multi-focal pattern warrants immediate clinical evaluation."
    
    return findings


def create_gradcam_visualization(original_image, preprocessed_img, model, confidence):
    """
    Generate complete Grad-CAM visualization including heatmap, overlay, and bounding boxes.
    
    Args:
        original_image: PIL Image (original upload)
        preprocessed_img: Preprocessed numpy array for model input
        model: Trained Keras model
        confidence: Model prediction confidence
    
    Returns:
        Tuple of (heatmap_array, overlay_image, heatmap_only_image, bbox_image, error_message, detailed_findings)
        - heatmap_array: Normalized activation heatmap
        - overlay_image: Heatmap overlaid on original image
        - heatmap_only_image: Standalone heatmap visualization
        - bbox_image: Original image with bounding boxes around detected regions (None if no regions)
        - error_message: Error string if generation failed, None otherwise
        - detailed_findings: Dictionary with extracted findings from the image
    """
    last_conv_layer_idx = get_last_conv_layer_index(model)
    
    if last_conv_layer_idx is None:
        error_msg = "No convolutional layer found in model"
        print(error_msg)
        return None, None, None, None, error_msg, None
    
    print(f"DEBUG: Found conv layer at index {last_conv_layer_idx}")
    print(f"DEBUG: Model has {len(model.layers)} layers")
    
    try:
        heatmap = make_gradcam_heatmap(preprocessed_img, model, last_conv_layer_idx)
        
        if heatmap is None:
            error_msg = "Heatmap generation returned None - gradient calculation may have failed"
            print(error_msg)
            return None, None, None, None, error_msg, None
        
        print(f"DEBUG: Heatmap generated successfully, shape: {heatmap.shape}")
        
        # Create tissue mask to filter out background detections
        img_array = np.array(original_image)
        tissue_mask = create_tissue_mask(img_array, threshold=15)
        
        overlay_image = create_heatmap_overlay(original_image, heatmap, alpha=0.5)
        print("DEBUG: Overlay created successfully")
        
        fig, ax = plt.subplots(figsize=(6, 6))
        im = ax.imshow(heatmap, cmap='jet')
        ax.axis('off')
        ax.set_title('Activation Heatmap', fontsize=14, fontweight='bold', pad=10)
        plt.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
        plt.tight_layout()
        
        # Convert matplotlib figure to PIL Image using buffer
        fig.canvas.draw()
        buf = np.frombuffer(fig.canvas.buffer_rgba(), dtype=np.uint8)
        buf = buf.reshape(fig.canvas.get_width_height()[::-1] + (4,))
        # Convert RGBA to RGB
        heatmap_only_image = Image.fromarray(buf[:, :, :3])
        plt.close(fig)
        
        # Generate bounding boxes for detected regions
        # Use tissue mask to ensure boxes only on breast tissue
        boxes = detect_bounding_boxes(heatmap, original_image.size, threshold=0.5, min_area=50, tissue_mask=tissue_mask)
        
        # Additional filter: remove boxes that are mostly on black background
        filtered_boxes = []
        img_h, img_w = img_array.shape[:2]
        for (x1, y1, x2, y2, conf) in boxes:
            # Ensure coordinates are within bounds
            x1s, y1s = max(0, int(x1)), max(0, int(y1))
            x2s, y2s = min(img_w-1, int(x2)), min(img_h-1, int(y2))
            
            if x2s <= x1s or y2s <= y1s:
                continue
            
            # Check if box center is on tissue
            cx, cy = (x1s + x2s) // 2, (y1s + y2s) // 2
            if not tissue_mask[cy, cx]:
                continue
            
            # Check tissue percentage in box (must be >40%)
            box_tissue = tissue_mask[y1s:y2s, x1s:x2s]
            if box_tissue.size > 0 and np.mean(box_tissue) < 0.4:
                continue
            
            filtered_boxes.append((x1, y1, x2, y2, conf))
        
        # Sort by confidence and limit to 10 regions max
        filtered_boxes = sorted(filtered_boxes, key=lambda b: b[4], reverse=True)[:10]
        
        bbox_image = None
        if filtered_boxes:
            bbox_image = draw_bounding_boxes(original_image, filtered_boxes, box_color='#FF0000', line_width=3)
            print(f"DEBUG: Detected {len(filtered_boxes)} suspicious regions")
            boxes = filtered_boxes  # Use filtered for findings
        else:
            # Fallback: show original image if no regions detected
            bbox_image = original_image.copy()
            print("DEBUG: No distinct high-activation regions detected, showing original")
        
        # Extract detailed findings
        detailed_findings = extract_detailed_findings(heatmap, boxes, original_image.size, confidence)
        print(f"DEBUG: Extracted findings: {detailed_findings['summary']}")
        
        print("DEBUG: Heatmap visualization complete!")
        return heatmap, overlay_image, heatmap_only_image, bbox_image, None, detailed_findings
        
    except Exception as e:
        error_msg = f"Error generating Grad-CAM: {str(e)}"
        print(error_msg)
        import traceback
        traceback.print_exc()
        return None, None, None, None, error_msg, None
