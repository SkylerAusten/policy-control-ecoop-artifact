"""
Utility module for converting HTML policy text to line-by-line images.
This prevents participants from copy-pasting policies into chatbots.
"""

import os
import hashlib
import re
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont


def strip_html_tags(text):
    """Remove HTML tags from text but preserve their visual representation."""
    # Remove opening and closing tags but keep the content
    text = re.sub(r'<[^>]+>', '', text)
    return text


def parse_html_for_styling(line):
    """
    Parse HTML line to extract text and color information.
    Returns a list of (text, color) tuples.
    """
    segments = []
    
    # Define color mappings based on CSS classes
    color_map = {
        'request-subject': '#4169e1',  # Royal blue
        'request-action': '#F26035',   # Orange
        'request-resource': '#009B55', # Green
    }
    
    # Default color is black
    default_color = '#000000'
    
    # Find all span tags with class attributes
    pattern = r'<span class="([^"]+)">([^<]+)</span>'
    
    last_end = 0
    for match in re.finditer(pattern, line):
        # Add text before the span (if any)
        if match.start() > last_end:
            plain_text = line[last_end:match.start()]
            if plain_text:
                segments.append((plain_text, default_color, False))
        
        # Add the span content with its color
        class_name = match.group(1)
        text = match.group(2)
        color = color_map.get(class_name, default_color)
        is_bold = 'subject' in class_name  # Make subjects bold
        segments.append((text, color, is_bold))
        
        last_end = match.end()
    
    # Add any remaining text after the last span
    if last_end < len(line):
        remaining = line[last_end:]
        if remaining:
            segments.append((remaining, default_color, False))
    
    return segments


def create_line_image(line, width=800, font_size=14):
    """
    Create an image for a single line of policy text.
    
    Args:
        line: The HTML line to convert
        width: Width of the image in pixels
        font_size: Font size in points
        
    Returns:
        PIL Image object
    """
    # Parse the line for styling
    segments = parse_html_for_styling(line)
    
    # If no segments (empty line), create a minimal image
    if not segments:
        # Use a smaller height for empty lines
        img = Image.new('RGBA', (width, font_size), color=(255, 255, 255, 0))
        return img
    
    # Try to use a monospace font for code
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", font_size)
        font_bold = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf", font_size)
    except:
        # Fallback to default font
        font = ImageFont.load_default()
        font_bold = font
    
    # Calculate total text width and height
    temp_img = Image.new('RGBA', (1, 1))
    temp_draw = ImageDraw.Draw(temp_img)
    
    # Calculate dimensions
    total_width = 0
    max_height = 0
    
    for text, color, is_bold in segments:
        current_font = font_bold if is_bold else font
        bbox = temp_draw.textbbox((0, 0), text, font=current_font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        total_width += text_width
        max_height = max(max_height, text_height)
    
    # Add some padding
    padding = 4
    img_height = max_height + 2 * padding
    
    # Create the actual image with transparent background
    img = Image.new('RGBA', (width, img_height), color=(255, 255, 255, 0))
    draw = ImageDraw.Draw(img)
    
    # Draw each segment
    x_offset = padding
    y_offset = padding
    
    for text, color, is_bold in segments:
        current_font = font_bold if is_bold else font
        draw.text((x_offset, y_offset), text, fill=color, font=current_font)
        bbox = draw.textbbox((x_offset, y_offset), text, font=current_font)
        x_offset = bbox[2]
    
    return img


def html_to_line_images(html_text, policy_key, cache_dir='static/policy_images', problem_id=None):
    """
    Convert HTML policy text to a list of image paths, one per line.
    
    Args:
        html_text: The HTML string containing the policy
        policy_key: Unique identifier for this policy (e.g., 'a', 'b', 'c', 'd')
        cache_dir: Directory to store generated images
        problem_id: Problem ID (e.g., 0, 1, 2) for naming files
        
    Returns:
        List of image paths (relative to static directory)
    """
    # Create cache directory if it doesn't exist
    os.makedirs(cache_dir, exist_ok=True)
    
    # Extract content from <pre> tags if present
    pre_match = re.search(r'<pre[^>]*>(.*?)</pre>', html_text, re.DOTALL)
    if pre_match:
        content = pre_match.group(1)
    else:
        content = html_text
    
    # Split into lines
    lines = content.split('\n')
    
    image_paths = []
    
    for i, line in enumerate(lines):
        # Create filename in format: problem#_policykey_line#.png
        if problem_id is not None:
            filename = f"{problem_id}_{policy_key}_{i}.png"
        else:
            # Fallback to hash-based naming if problem_id not provided
            policy_hash = hashlib.md5(html_text.encode()).hexdigest()[:8]
            filename = f"{policy_key}_{policy_hash}_line_{i}.png"
        
        filepath = os.path.join(cache_dir, filename)
        
        # Generate image for this line if it doesn't exist
        if not os.path.exists(filepath):
            img = create_line_image(line)
            img.save(filepath, 'PNG')
        
        # Store relative path for use in HTML
        relative_path = f"policy_images/{filename}"
        image_paths.append(relative_path)
    
    return image_paths


def generate_policy_images_dict(policy_options, problem_id=None):
    """
    Get references to pre-generated policy images.
    
    Note: Images should be pre-generated using scripts/generate_policy_images.py
    This function just creates references to the existing images without generating them.
    
    Args:
        policy_options: List of policy option dictionaries with 'key' and 'html' fields
        problem_id: Problem ID (e.g., 0, 1, 2) for naming files
        
    Returns:
        Dictionary mapping policy keys to lists of image paths
    """
    policy_images = {}
    
    for option in policy_options:
        key = option['key']
        html = option['html']
        
        # Skip special options (none, unsure) - they don't need images
        if key in ['none', 'unsure']:
            policy_images[key] = None
        else:
            # Get references to pre-generated images (without creating new ones)
            image_paths = get_policy_image_paths(html, key, problem_id)
            policy_images[key] = image_paths
    
    return policy_images


def get_policy_image_paths(html_text, policy_key, problem_id=None):
    """
    Get paths to pre-generated policy line images without creating them.
    
    Args:
        html_text: The HTML string containing the policy
        policy_key: Unique identifier for this policy
        problem_id: Problem ID (e.g., 0, 1, 2) for naming files
        
    Returns:
        List of image paths (relative to static directory)
    """
    # Extract content from <pre> tags if present
    pre_match = re.search(r'<pre[^>]*>(.*?)</pre>', html_text, re.DOTALL)
    if pre_match:
        content = pre_match.group(1)
    else:
        content = html_text
    
    # Split into lines
    lines = content.split('\n')
    
    image_paths = []
    
    for i in range(len(lines)):
        # Create filename in format: problem#_policykey_line#.png
        if problem_id is not None:
            filename = f"{problem_id}_{policy_key}_{i}.png"
        else:
            # Fallback to hash-based naming if problem_id not provided
            policy_hash = hashlib.md5(html_text.encode()).hexdigest()[:8]
            filename = f"{policy_key}_{policy_hash}_line_{i}.png"
        
        # Store relative path for use in HTML
        relative_path = f"policy_images/{filename}"
        image_paths.append(relative_path)
    
    return image_paths
