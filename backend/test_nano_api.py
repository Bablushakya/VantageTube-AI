#!/usr/bin/env python3
"""
Test script for Nano API thumbnail generation
"""

import asyncio
import sys
import os

# Add the backend directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.nano_service import nano_service


async def test_nano_api():
    """Test Nano API thumbnail generation"""
    print("=" * 60)
    print("Testing Nano API Thumbnail Generation")
    print("=" * 60)
    
    # Test 1: Basic thumbnail generation
    print("\n[TEST 1] Basic thumbnail generation...")
    try:
        result = await nano_service.generate_thumbnail(
            topic="AI Will Replace You in 2026",
            title="AI Will Replace You in 2026",
            style="modern",
            color_scheme="vibrant"
        )
        
        print(f"✓ Generated thumbnail")
        print(f"  - URL: {result.get('thumbnail_url', 'N/A')}")
        print(f"  - Model: {result.get('model', 'N/A')}")
        print(f"  - Generated: {result.get('generated', False)}")
        print(f"  - Style: {result.get('style', 'N/A')}")
        
    except Exception as e:
        print(f"✗ Error: {e}")
    
    # Test 2: Different style
    print("\n[TEST 2] Bold style thumbnail...")
    try:
        result = await nano_service.generate_thumbnail(
            topic="Mobile vs Laptop",
            title="Mobile vs Laptop",
            style="bold",
            color_scheme="dark"
        )
        
        print(f"✓ Generated thumbnail")
        print(f"  - URL: {result.get('thumbnail_url', 'N/A')}")
        print(f"  - Model: {result.get('model', 'N/A')}")
        print(f"  - Generated: {result.get('generated', False)}")
        
    except Exception as e:
        print(f"✗ Error: {e}")
    
    # Test 3: Multiple thumbnails
    print("\n[TEST 3] Multiple thumbnail variations...")
    try:
        result = await nano_service.generate_multiple_thumbnails(
            topic="YouTube SEO Tips",
            title="YouTube SEO Tips",
            count=2
        )
        
        print(f"✓ Generated {result.get('count', 0)} thumbnails")
        for i, thumb in enumerate(result.get('thumbnails', []), 1):
            print(f"  - Thumbnail {i}: {thumb.get('model', 'N/A')}")
        
    except Exception as e:
        print(f"✗ Error: {e}")
    
    print("\n" + "=" * 60)
    print("Testing complete!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_nano_api())
