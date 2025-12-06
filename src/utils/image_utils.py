import requests
from PIL import Image, ImageEnhance, ImageOps, ImageFilter
from io import BytesIO
import os
import logging
import hashlib
import tempfile
import subprocess
import numpy as np

logger = logging.getLogger(__name__)

def get_image(image_url):
    response = requests.get(image_url)
    img = None
    if 200 <= response.status_code < 300 or response.status_code == 304:
        img = Image.open(BytesIO(response.content))
    else:
        logger.error(f"Received non-200 response from {image_url}: status_code: {response.status_code}")
    return img

def change_orientation(image, orientation, inverted=False):
    if orientation == 'horizontal':
        angle = 0
    elif orientation == 'vertical':
        angle = 90

    if inverted:
        angle = (angle + 180) % 360

    return image.rotate(angle, expand=1)

def resize_image(image, desired_size, image_settings=[]):
    img_width, img_height = image.size
    desired_width, desired_height = desired_size
    desired_width, desired_height = int(desired_width), int(desired_height)

    img_ratio = img_width / img_height
    desired_ratio = desired_width / desired_height

    keep_width = "keep-width" in image_settings

    x_offset, y_offset = 0,0
    new_width, new_height = img_width,img_height
    # Step 1: Determine crop dimensions
    desired_ratio = desired_width / desired_height
    if img_ratio > desired_ratio:
        # Image is wider than desired aspect ratio
        new_width = int(img_height * desired_ratio)
        if not keep_width:
            x_offset = (img_width - new_width) // 2
    else:
        # Image is taller than desired aspect ratio
        new_height = int(img_width / desired_ratio)
        if not keep_width:
            y_offset = (img_height - new_height) // 2

    # Step 2: Crop the image
    image = image.crop((x_offset, y_offset, x_offset + new_width, y_offset + new_height))

    # Step 3: Resize to the exact desired dimensions (if necessary)
    return image.resize((desired_width, desired_height), Image.LANCZOS)

def apply_image_enhancement(img, image_settings={}):

    # Apply Brightness
    img = ImageEnhance.Brightness(img).enhance(image_settings.get("brightness", 1.0))

    # Apply Contrast
    img = ImageEnhance.Contrast(img).enhance(image_settings.get("contrast", 1.0))

    # Apply Saturation (Color)
    img = ImageEnhance.Color(img).enhance(image_settings.get("saturation", 1.0))

    # Apply Sharpness
    img = ImageEnhance.Sharpness(img).enhance(image_settings.get("sharpness", 1.0))

    return img

def compute_image_hash(image):
    """Compute SHA-256 hash of an image."""
    image = image.convert("RGB")
    img_bytes = image.tobytes()
    return hashlib.sha256(img_bytes).hexdigest()

def take_screenshot_html(html_str, dimensions, timeout_ms=None):
    image = None
    try:
        # Create a temporary HTML file
        with tempfile.NamedTemporaryFile(suffix=".html", delete=False) as html_file:
            html_file.write(html_str.encode("utf-8"))
            html_file_path = html_file.name

        image = take_screenshot(html_file_path, dimensions, timeout_ms)

        # Remove html file
        os.remove(html_file_path)

    except Exception as e:
        logger.error(f"Failed to take screenshot: {str(e)}")

    return image

def take_screenshot(target, dimensions, timeout_ms=None):
    image = None
    try:
        # Create a temporary output file for the screenshot
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as img_file:
            img_file_path = img_file.name

        width, height = dimensions
        logger.info(f"Taking screenshot: target={target}, dimensions={dimensions}")

        chromium_path = os.getenv("CHROMIUM_PATH", "chromium-headless-shell")

        command = [
            chromium_path,
            target,
            "--headless",
            f"--screenshot={img_file_path}",
            f"--window-size={dimensions[0]},{dimensions[1]}",
            f"--force-device-scale-factor=1",
            "--virtual-time-budget=3000",
            "--disable-dev-shm-usage",
            "--disable-gpu",
            "--use-gl=swiftshader",
            "--hide-scrollbars",
            "--in-process-gpu",
            "--js-flags=--jitless",
            "--disable-zero-copy",
            "--disable-gpu-memory-buffer-compositor-resources",
            "--disable-extensions",
            "--disable-plugins",
            "--mute-audio",
            "--no-sandbox"
        ]
        if timeout_ms:
            command.append(f"--timeout={timeout_ms}")
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        logger.info(f"Chrome command: {' '.join(command)}")
        logger.info(f"Chrome returned: {result.returncode}")
        if result.stderr:
            logger.info(f"Chrome stderr: {result.stderr.decode('utf-8')[:500]}")

        # Check if the process failed or the output file is missing
        if result.returncode != 0 or not os.path.exists(img_file_path):
            logger.error("Failed to take screenshot:")
            logger.info(f"Chrome returned: {result.returncode}")
            if result.stderr:
                logger.error(f"Full Chrome stderr: {result.stderr.decode('utf-8')}")
            return None

        # Load the image using PIL
        with Image.open(img_file_path) as img:
            image = img.copy()
            
        logger.info(f"Screenshot successful: dimensions={[width, height]}, output size: {image.size}")

        # Remove image files
        os.remove(img_file_path)

    except Exception as e:
        logger.error(f"Failed to take screenshot: {str(e)}")

    return image

def pad_image_blur(img: Image, dimensions: tuple[int, int]) -> Image:
    bkg = ImageOps.fit(img, dimensions)
    bkg = bkg.filter(ImageFilter.BoxBlur(8))
    img = ImageOps.contain(img, dimensions)

    img_size = img.size
    bkg.paste(img, ((dimensions[0] - img_size[0]) // 2, (dimensions[1] - img_size[1]) // 2))
    return bkg

def get_e6_palette(palette_type='standard'):
    """
    Get E6 display color palette.

    Args:
        palette_type (str): 'standard' (pure RGB colors), 'tuned' (Waveshare C++ tool adjusted colors), or 'original' (InkyPi original - no optimization)

    Returns:
        list: RGB color values for 6 colors, or extended palette for official compatibility
    """
    if palette_type == 'original':
        return None

    palettes = {
        'standard': [
            0, 0, 0,        # Black   - RGB(0, 0, 0)
            255, 255, 255,  # White   - RGB(255, 255, 255)
            255, 255, 0,    # Yellow  - RGB(255, 255, 0) - Pure yellow
            255, 0, 0,      # Red     - RGB(255, 0, 0) - Pure red
            0, 0, 255,      # Blue    - RGB(0, 0, 255) - Pure blue
            0, 255, 0       # Green   - RGB(0, 255, 0) - Pure green
        ],
        'tuned': [
            0, 0, 0,        # Black   - RGB(0, 0, 0)
            255, 255, 255,  # White   - RGB(255, 255, 255)
            255, 243, 56,   # Yellow  - RGB(255, 243, 56) - Adjusted for e-ink
            191, 0, 0,      # Red     - RGB(191, 0, 0) - Darker red for better contrast
            100, 64, 255,   # Blue    - RGB(100, 64, 255) - Purple-blue for e-ink
            67, 138, 28     # Green   - RGB(67, 138, 28) - Darker green
        ],
        'standard_official': [
            0, 0, 0,        # Black   - RGB(0, 0, 0)
            255, 255, 255,  # White   - RGB(255, 255, 255)
            255, 255, 0,    # Yellow  - RGB(255, 255, 0) - Pure yellow
            255, 0, 0,      # Red     - RGB(255, 0, 0) - Pure red
            0, 0, 0,        # Index 4 - Skip position (orange placeholder, unused for E6)
            0, 0, 255,      # Blue    - RGB(0, 0, 255) - Pure blue (now at index 5)
            0, 255, 0       # Green   - RGB(0, 255, 0) - Pure green (now at index 6)
        ],
        'tuned_official': [
            0, 0, 0,        # Black   - RGB(0, 0, 0)
            255, 255, 255,  # White   - RGB(255, 255, 255)
            255, 243, 56,   # Yellow  - RGB(255, 243, 56) - Adjusted for e-ink
            191, 0, 0,      # Red     - RGB(191, 0, 0) - Darker red for better contrast
            0, 0, 0,        # Index 4 - Skip position (orange placeholder, unused for E6)
            100, 64, 255,   # Blue    - RGB(100, 64, 255) - Purple-blue for e-ink (now at index 5)
            67, 138, 28     # Green   - RGB(67, 138, 28) - Darker green (now at index 6)
        ]
    }
    return palettes.get(palette_type, palettes['standard'])

def optimize_for_e6_display(image, display_type, palette_type='standard', comparison_mode=False):
    """
    Optimize image for Waveshare e6 (ACeP) displays with palette-based color quantization.

    Args:
        image (PIL.Image): Source image to optimize (should already have enhancements applied)
        display_type (str): Display model identifier (e.g., 'epd7in3e')
        palette_type (str): 'standard', 'tuned', or 'original' palette
        comparison_mode (bool): If True, split image to show both palettes side by side

    Returns:
        PIL.Image: Optimized image for e6 display
    """

    if 'e' not in display_type.lower() or 'epd' not in display_type.lower():
        return image

    logger.info(f"Applying e6 display optimization for {display_type}")
    logger.info(f"Palette type: {palette_type}, Comparison mode: {comparison_mode}")

    image = image.convert('RGB')

    if comparison_mode:
        return _create_comparison_image(image, display_type)

    if palette_type == 'original':
        logger.info("Using original InkyPi mode (no e6 optimization)")
        return image

    # Determine actual palette type and algorithm type
    actual_palette_type = palette_type
    algorithm_type = None
    
    if palette_type.endswith('_official'):
        actual_palette_type = palette_type.replace('_official', '')
        algorithm_type = 'official'
    elif palette_type.endswith('_ordered'):
        actual_palette_type = palette_type.replace('_ordered', '')
        algorithm_type = 'ordered'
    
    e6_palette = get_e6_palette(actual_palette_type)

    # Apply algorithm based on type
    if algorithm_type == 'official':
        logger.info(f"Using official euclidean distance algorithm with {actual_palette_type} palette")
        return _apply_official_quantization(image, e6_palette)
    else:
        # Use PIL quantization - support different dithering algorithms
        palette_image = Image.new('P', (1, 1))
        palette_image.putpalette(e6_palette + [0] * (768 - len(e6_palette)))
        
        # Determine dithering algorithm
        if algorithm_type == 'ordered':
            optimized = image.quantize(palette=palette_image, dither=Image.Dither.ORDERED)
            logger.info(f"Using ORDERED dithering with {actual_palette_type} palette")
        else:
            # Default Floyd-Steinberg dithering
            optimized = image.quantize(palette=palette_image, dither=Image.Dither.FLOYDSTEINBERG)
            logger.info(f"Using Floyd-Steinberg dithering with {actual_palette_type} palette")
        
        # Return indexed image (P mode) instead of RGB to preserve quantization
        return optimized

def _apply_official_quantization(image, e6_palette):
    """
    Apply official Waveshare euclidean distance quantization algorithm.
    Replicated from converterTo6color.cpp for authentic color mapping.
    """
    logger.info("Applying official euclidean distance quantization")
    
    width, height = image.size
    result_image = Image.new('P', (width, height))
    
    # Convert flat palette to RGB tuples for easier access
    palette_colors = [(e6_palette[i], e6_palette[i+1], e6_palette[i+2]) 
                    for i in range(0, len(e6_palette), 3)]
    
    result_pixels = []
    
    for y in range(height):
        for x in range(width):
            pixel = image.getpixel((x, y))
            
            # Find closest color using euclidean distance (official algorithm)
            min_dist = 100000000
            best_idx = 0
            
            for color_idx, color in enumerate(palette_colors):
                # Calculate euclidean distance in RGB space
                diff_r = pixel[0] - color[0]
                diff_g = pixel[1] - color[1] 
                diff_b = pixel[2] - color[2]
                distance = (diff_r * diff_r) + (diff_g * diff_g) + (diff_b * diff_b)
                
                if distance < min_dist:
                    min_dist = distance
                    best_idx = color_idx
            
            # Apply official index correction for 6-color displays
            # Skip index 4 for hardware compatibility (matches converterTo6color.cpp)
            if best_idx > 3:
                best_idx = best_idx + 1
            
            result_pixels.append(best_idx)
    
    # Convert back to image with quantized palette
    result_image.putdata(result_pixels)
    result_image.putpalette(e6_palette + [0] * (768 - len(e6_palette)))
    
    # Return indexed image (P mode) instead of RGB to preserve quantization
    return result_image

def _create_comparison_image(image, display_type):
    """
    Create side-by-side comparison of Floyd-Steinberg vs Ordered dithering.
    Left: Floyd-Steinberg dithering, Right: Ordered dithering

    Args:
        image (PIL.Image): Source image (should already have enhancements applied)
        display_type (str): Display model identifier

    Returns:
        PIL.Image: Split image comparing Floyd-Steinberg vs Ordered dithering
    """
    logger.info("Creating dithering comparison image (left: Floyd-Steinberg, right: Ordered)")

    width, height = image.size
    half_width = width // 2

    left_part = image.crop((0, 0, half_width, height))
    right_part = image.crop((half_width, 0, width, height))

    # Get palette type for comparison
    palette_type = 'standard'  # Default palette for comparison
    e6_palette = get_e6_palette(palette_type)
    
    # Left: Floyd-Steinberg dithering
    floyd_palette = Image.new('P', (1, 1))
    floyd_palette.putpalette(e6_palette + [0] * (768 - len(e6_palette)))
    optimized_left = left_part.quantize(palette=floyd_palette, dither=Image.Dither.FLOYDSTEINBERG).convert('RGB')

    # Right: Ordered dithering
    ordered_palette = Image.new('P', (1, 1))
    ordered_palette.putpalette(e6_palette + [0] * (768 - len(e6_palette)))
    optimized_right = right_part.quantize(palette=ordered_palette, dither=Image.Dither.ORDERED).convert('RGB')

    result = Image.new('RGB', (width, height))
    result.paste(optimized_left, (0, 0))
    result.paste(optimized_right, (half_width, 0))

    return result