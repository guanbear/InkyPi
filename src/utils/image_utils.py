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

        chromium_path = os.getenv("CHROMIUM_PATH", "chromium-headless-shell")

        command = [
            chromium_path,
            target,
            "--headless",
            f"--screenshot={img_file_path}",
            f"--window-size={dimensions[0]},{dimensions[1]}",
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

        # Check if the process failed or the output file is missing
        if result.returncode != 0 or not os.path.exists(img_file_path):
            logger.error("Failed to take screenshot:")
            logger.error(result.stderr.decode('utf-8'))
            return None

        # Load the image using PIL
        with Image.open(img_file_path) as img:
            image = img.copy()

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
        list: RGB color values for 6 colors, or None for original (no palette optimization)
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
        ]
    }
    return palettes.get(palette_type, palettes['standard'])

def optimize_for_e6_display(image, display_type, palette_type='standard', comparison_mode=False):
    """
    Optimize image for Waveshare e6 (ACeP) displays with improved color mapping and dithering.

    Args:
        image (PIL.Image): Source image to optimize
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

    # Original InkyPi mode - no optimization
    if palette_type == 'original':
        logger.info("Using original InkyPi mode (no e6 optimization)")
        return image

    e6_palette = get_e6_palette(palette_type)

    palette_image = Image.new('P', (1, 1))
    palette_image.putpalette(e6_palette + [0] * (768 - len(e6_palette)))

    # Enhanced image processing for better E6 display quality
    # Waveshare official recommended settings
    enhanced = ImageEnhance.Color(image).enhance(1.2)  # Saturation: 1.2

    # Normal contrast for better color accuracy
    enhanced = ImageEnhance.Contrast(enhanced).enhance(1.0)  # Contrast: 1.0

    # Slight sharpness improvement
    enhanced = ImageEnhance.Sharpness(enhanced).enhance(1.1)  # Sharpness: 1.1

    # Normal brightness
    enhanced = ImageEnhance.Brightness(enhanced).enhance(1.0)  # Brightness: 1.0

    # 4.使用Floyd-Steinberg抖动算法进行色彩量化
    optimized = enhanced.quantize(palette=palette_image, dither=Image.Dither.FLOYDSTEINBERG)

    return optimized.convert('RGB')

def _create_comparison_image(image, display_type):
    """
    Create side-by-side comparison of different palettes.
    Left: standard, Middle: tuned, Right: original (no optimization)

    Args:
        image (PIL.Image): Source image
        display_type (str): Display model identifier

    Returns:
        PIL.Image: Split image with three palettes
    """
    logger.info("Creating palette comparison image (left: standard, middle: tuned, right: original)")

    width, height = image.size
    third_width = width // 3

    # Split image into three parts
    left_part = image.crop((0, 0, third_width, height))
    middle_part = image.crop((third_width, 0, third_width * 2, height))
    right_part = image.crop((third_width * 2, 0, width, height))

    # Apply standard palette to left
    standard_palette = get_e6_palette('standard')
    standard_pal_image = Image.new('P', (1, 1))
    standard_pal_image.putpalette(standard_palette + [0] * (768 - len(standard_palette)))

    # Apply tuned palette to middle
    tuned_palette = get_e6_palette('tuned')
    tuned_pal_image = Image.new('P', (1, 1))
    tuned_pal_image.putpalette(tuned_palette + [0] * (768 - len(tuned_palette)))

    # Enhance left and middle parts
    enhanced_left = ImageEnhance.Color(left_part).enhance(1.2)
    enhanced_left = ImageEnhance.Contrast(enhanced_left).enhance(1.0)
    enhanced_left = ImageEnhance.Sharpness(enhanced_left).enhance(1.1)
    enhanced_left = ImageEnhance.Brightness(enhanced_left).enhance(1.0)

    enhanced_middle = ImageEnhance.Color(middle_part).enhance(1.2)
    enhanced_middle = ImageEnhance.Contrast(enhanced_middle).enhance(1.0)
    enhanced_middle = ImageEnhance.Sharpness(enhanced_middle).enhance(1.1)
    enhanced_middle = ImageEnhance.Brightness(enhanced_middle).enhance(1.0)

    # Quantize left and middle with palettes
    optimized_left = enhanced_left.quantize(palette=standard_pal_image, dither=Image.Dither.FLOYDSTEINBERG).convert('RGB')
    optimized_middle = enhanced_middle.quantize(palette=tuned_pal_image, dither=Image.Dither.FLOYDSTEINBERG).convert('RGB')

    # Right part stays original (no optimization)
    optimized_right = right_part

    # Combine three parts
    result = Image.new('RGB', (width, height))
    result.paste(optimized_left, (0, 0))
    result.paste(optimized_middle, (third_width, 0))
    result.paste(optimized_right, (third_width * 2, 0))

    return result