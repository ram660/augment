"""
Quick Test Script for Design Studio Transformation

Usage:
    python backend/tests/quick_test_transformation.py <image_path>
    python backend/tests/quick_test_transformation.py backend/tests/test_images/kitchen.jpg

This script performs a quick transformation test and shows all API calls.
"""

import asyncio
import sys
import os
from pathlib import Path
import json
from PIL import Image
import io

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.services.design_transformation_service import DesignTransformationService


async def quick_test(image_path: str):
    """Quick transformation test."""
    
    print("\n" + "="*80)
    print("🏠 HomeView AI - Quick Transformation Test".center(80))
    print("="*80 + "\n")
    
    # Load image
    print(f"📸 Loading image: {image_path}")
    with open(image_path, 'rb') as f:
        image_bytes = f.read()
    pil_image = Image.open(io.BytesIO(image_bytes))
    print(f"✅ Image loaded: {pil_image.size[0]}x{pil_image.size[1]} pixels\n")
    
    # Initialize service
    print("🔧 Initializing services...")
    service = DesignTransformationService()
    print("✅ Services ready\n")
    
    # Transform
    prompt = "Modern minimalist style with white walls and light wood flooring"
    print(f"🎨 Transformation prompt: '{prompt}'")
    print("⏳ Transforming image (this may take 30-60 seconds)...\n")
    
    try:
        # 🚀 Use Gemini 2.5 Flash Image for BOTH transform + analyze in ONE call!
        print("="*80)
        print("🚀 USING NEW GEMINI 2.5 FLASH IMAGE MODEL".center(80))
        print("   This model can do BOTH transformation AND analysis in ONE API call!".center(80))
        print("="*80)
        print("\nAPI Call 1/2: Gemini 2.5 Flash Image - transform_and_analyze()")
        print("   🎯 This ONE call does EVERYTHING:")
        print("      • Transform image with prompt")
        print("      • Analyze transformed result comprehensively")
        print("      • Colors, Materials, Styles, Description")
        print("      • Room Dimensions, Openings, Object Counts")
        print("      • Surface Areas (floor, walls, ceiling)")
        print("      • Material Quantities (paint, flooring, baseboard, tiles)")
        print("   ⏳ Transforming and analyzing...")

        try:
            result = await service.gemini.transform_and_analyze_with_gemini_2_5_flash_image(
                image=pil_image,
                transformation_prompt=prompt,
                room_hint="kitchen"
            )

            transformed_image = result["transformed_image"]
            analysis = result["analysis"]

            # Convert to bytes for product search
            img_buffer = io.BytesIO()
            transformed_image.save(img_buffer, format='JPEG')
            transformed_bytes = img_buffer.getvalue()

            print(f"✅ Transform + Analysis complete in ONE API call!")
            print(f"   Model used: {result['model_used']}\n")

        except Exception as e:
            print(f"⚠️  Gemini 2.5 Flash Image not available: {str(e)}")
            print("   Falling back to separate calls...\n")

            # Fallback to old method
            print("API Call 1/3: Gemini Imagen - edit_image()")
            transformed = await service.gemini.edit_image(prompt=prompt, reference_image=pil_image, num_images=1)
            print(f"✅ Transformation complete! Generated {len(transformed)} variation(s)\n")

            # Convert to bytes
            img_buffer = io.BytesIO()
            transformed[0].save(img_buffer, format='JPEG')
            transformed_bytes = img_buffer.getvalue()

            # 2. UNIFIED HOME IMPROVEMENT ANALYSIS
            print("API Call 2/3: Gemini Vision - analyze_home_improvement_image()")
            print("   🎯 This ONE call returns EVERYTHING:")
            print("      • Colors, Materials, Styles, Description")
            print("      • Room Dimensions, Openings, Object Counts")
            print("      • Surface Areas (floor, walls, ceiling)")
            print("      • Material Quantities (paint, flooring, baseboard, tiles)")
            print("   ⏳ Analyzing...")

            analysis = await service.gemini.analyze_home_improvement_image(image=transformed_bytes)

        print("✅ Complete analysis done in ONE API call!\n")

        # Extract all data
        colors = analysis.get('colors', [])
        materials = analysis.get('materials', [])
        styles = analysis.get('styles', [])
        description = analysis.get('description', '')
        dimensions = analysis.get('dimensions', {})
        openings = analysis.get('openings', {})
        object_counts = analysis.get('object_counts', {})
        areas = analysis.get('areas', {})
        quantities = analysis.get('quantities', {})
        assumptions = analysis.get('assumptions', [])
        confidence = analysis.get('confidence', 'unknown')

        # Display results
        print(f"   🎨 Colors ({len(colors)}):")
        for color in colors[:5]:
            if isinstance(color, dict):
                print(f"      • {color.get('name', 'Unknown')} - {color.get('hex', '#000000')} - RGB{color.get('rgb', [0,0,0])}")
            else:
                print(f"      • {color}")

        print(f"\n   🏗️  Materials ({len(materials)}):")
        for material in materials[:5]:
            print(f"      • {material}")

        print(f"\n   ✨ Styles ({len(styles)}):")
        for style in styles[:3]:
            print(f"      • {style}")

        print(f"\n   📝 Description:")
        print(f"      {description}")

        print(f"\n   📐 Room Dimensions:")
        Lm = dimensions.get('length_m')
        Wm = dimensions.get('width_m')
        Hm = dimensions.get('height_m')
        if Lm and Wm and Hm:
            print(f"      {Lm}m × {Wm}m × {Hm}m ({Lm*3.281:.1f}ft × {Wm*3.281:.1f}ft × {Hm*3.281:.1f}ft)")
        else:
            print(f"      {Lm}m × {Wm}m × {Hm}m")

        print(f"\n   🪟 Openings:")
        print(f"      Windows: {openings.get('windows', 0)}")
        print(f"      Doors: {openings.get('doors', 0)}")

        print(f"\n   🪑 Object Counts:")
        for obj, count in list(object_counts.items())[:5]:
            print(f"      {obj}: {count}")

        print(f"\n   📏 Surface Areas:")
        if areas:
            print(f"      Floor: {areas.get('floor_m2', 0)} m² ({areas.get('floor_sqft', 0)} ft²)")
            print(f"      Walls: {areas.get('walls_m2', 0)} m² ({areas.get('walls_sqft', 0)} ft²)")
            print(f"      Ceiling: {areas.get('ceiling_m2', 0)} m² ({areas.get('ceiling_sqft', 0)} ft²)")

        print(f"\n   🛒 Material Quantities:")
        if quantities:
            if quantities.get('paint_gallons_two_coats'):
                print(f"      Paint: {quantities['paint_gallons_two_coats']} gallons ({quantities.get('paint_liters_two_coats', 0)} L) for 2 coats")
            if quantities.get('flooring_sqft'):
                print(f"      Flooring: {quantities['flooring_sqft']} ft² ({quantities.get('flooring_m2', 0)} m²) with 10% waste")
            if quantities.get('baseboard_linear_ft'):
                print(f"      Baseboard: {quantities['baseboard_linear_ft']} linear ft ({quantities.get('baseboard_linear_m', 0)} m)")
            if quantities.get('tile_30x60cm_count'):
                print(f"      Tiles (30×60cm): {quantities['tile_30x60cm_count']} tiles")

        print(f"\n   📊 Confidence: {confidence}")
        print(f"\n   💡 Assumptions:")
        for assumption in assumptions[:3]:
            print(f"      • {assumption}")
        print()

        # 2. Products
        print("API Call 2/2: Google Grounding - suggest_products_with_grounding()")

        # Build grounding payload
        grounding_payload = {
            "user_prompt": prompt,
            "requested_changes": ["paint", "flooring", "decor"],
            "new_summary": analysis,
            "location_hint": "Vancouver, Canada"
        }

        product_response = await service.gemini.suggest_products_with_grounding(
            summary_or_grounding=grounding_payload,
            max_items=10
        )

        if product_response.success:
            products = product_response.data.get('products', [])
            print(f"✅ Found {len(products)} product recommendations")
            print(f"   💰 API Cost: ${product_response.cost_usd:.4f}")
            print(f"   ⏱️  Latency: {product_response.latency_ms}ms")
            print(f"   📦 Cached: {product_response.cached}")

            for idx, product in enumerate(products[:3], 1):
                print(f"\n   🛒 Product {idx}: {product.get('name', 'Unknown Product')}")
                print(f"      Category: {product.get('category', 'N/A')}")
                print(f"      Price: {product.get('price', 'N/A')}")
                print(f"      URL: {product.get('url', 'N/A')[:60]}...")
        else:
            print(f"❌ Product search failed")
        print()
        
        # Summary
        print("="*80)
        print("✅ Test Complete!".center(80))
        print("="*80)
        print("\n📊 Summary:")
        print(f"   • Colors: {len(colors)} with hex codes")
        print(f"   • Materials: {len(materials)}")
        print(f"   • Styles: {len(styles)}")
        print(f"   • Room Dimensions: {Lm}×{Wm}×{Hm}m")

        # Get paint quantities
        paint_data = quantities.get('paint', {})
        if paint_data:
            walls_paint = paint_data.get('walls_only', {}).get('two_coats', {})
            if walls_paint:
                print(f"   • Paint Needed: {walls_paint.get('gallons', 'N/A')} gallons")

        # Get flooring quantities
        flooring_data = quantities.get('flooring', {})
        if flooring_data:
            hardwood = flooring_data.get('hardwood', {})
            if hardwood:
                print(f"   • Flooring Needed: {hardwood.get('sqft', 'N/A')} ft²")

        if product_response.success:
            print(f"   • Products Found: {len(products)}")

        print("\n🎉 API Call Optimization Complete!")
        print("   ✅ OLD APPROACH: 6 separate API calls")
        print("      1. Imagen (transform)")
        print("      2-5. Multiple analysis calls")
        print("      6. Product search")
        print("\n   ✅ PREVIOUS OPTIMIZATION: 3 API calls")
        print("      1. Imagen (transform)")
        print("      2. Unified analysis")
        print("      3. Product search")
        print("\n   🚀 NEW WITH GEMINI 2.5 FLASH IMAGE: 2 API calls!")
        print("      1. Gemini 2.5 Flash Image (transform + analyze in ONE call!)")
        print("      2. Product search")
        print("\n   💰 67% reduction in API calls!")
        print("   ⚡ Faster, cheaper, and more comprehensive!\n")
        
    except Exception as e:
        print(f"\n❌ Error: {e}\n")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("\n❌ Usage: python backend/tests/quick_test_transformation.py <image_path>")
        print("\nExample:")
        print("   python backend/tests/quick_test_transformation.py backend/tests/test_images/kitchen.jpg")
        print()
        sys.exit(1)
    
    image_path = sys.argv[1]
    
    if not os.path.exists(image_path):
        print(f"\n❌ Error: Image not found at: {image_path}\n")
        sys.exit(1)
    
    asyncio.run(quick_test(image_path))

