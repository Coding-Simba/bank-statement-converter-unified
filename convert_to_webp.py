#!/usr/bin/env python3
"""
Convert PNG/JPG images to WebP format for better compression
Requires: pip install pillow
"""

import os
from pathlib import Path
try:
    from PIL import Image
except ImportError:
    print("❌ Pillow library not installed.")
    print("   Install with: pip install pillow")
    exit(1)

def convert_to_webp(image_path, quality=85):
    """Convert an image to WebP format"""
    try:
        # Open the image
        img = Image.open(image_path)
        
        # Create WebP filename
        webp_path = image_path.with_suffix('.webp')
        
        # Save as WebP
        img.save(webp_path, 'WEBP', quality=quality, method=6)
        
        # Get file sizes
        original_size = image_path.stat().st_size
        webp_size = webp_path.stat().st_size
        reduction = ((original_size - webp_size) / original_size) * 100
        
        return True, original_size, webp_size, reduction
    except Exception as e:
        return False, 0, 0, 0

def main():
    """Convert all PNG/JPG images to WebP"""
    print("🖼️  WebP Image Converter")
    print("=" * 50)
    
    # Find all PNG and JPG images
    image_extensions = ['.png', '.jpg', '.jpeg']
    image_files = []
    
    for ext in image_extensions:
        image_files.extend(Path('assets').glob(f'*{ext}'))
        image_files.extend(Path('.').glob(f'*{ext}'))
    
    if not image_files:
        print("ℹ️  No PNG or JPG images found to convert")
        print("   All images are already in SVG format (optimal for icons)")
        return
    
    print(f"Found {len(image_files)} images to convert")
    
    total_original = 0
    total_webp = 0
    converted = 0
    
    for image_path in image_files:
        print(f"\nConverting: {image_path}")
        success, orig_size, webp_size, reduction = convert_to_webp(image_path)
        
        if success:
            converted += 1
            total_original += orig_size
            total_webp += webp_size
            print(f"  ✅ Converted successfully")
            print(f"     Original: {orig_size:,} bytes")
            print(f"     WebP: {webp_size:,} bytes")
            print(f"     Reduction: {reduction:.1f}%")
        else:
            print(f"  ❌ Conversion failed")
    
    if converted > 0:
        total_reduction = ((total_original - total_webp) / total_original) * 100
        print("\n" + "=" * 50)
        print(f"✅ Conversion Complete!")
        print(f"   Images converted: {converted}")
        print(f"   Total original size: {total_original:,} bytes")
        print(f"   Total WebP size: {total_webp:,} bytes")
        print(f"   Total reduction: {total_reduction:.1f}%")
        
        print("\n💡 Next Steps:")
        print("   1. Update HTML/CSS to use .webp files")
        print("   2. Keep original files as fallback")
        print("   3. Use <picture> element for compatibility:")
        print("""
      <picture>
        <source srcset="image.webp" type="image/webp">
        <img src="image.png" alt="Description">
      </picture>
        """)

if __name__ == "__main__":
    main()