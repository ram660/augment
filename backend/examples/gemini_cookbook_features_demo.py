"""
Demo script showcasing the new Gemini Cookbook features in HomeView AI.

This script demonstrates:
1. Enhanced Spatial Analysis (bounding boxes, segmentation)
2. Multi-Image Sequence Analysis
3. Structured Content Generation (DIY instructions)
4. Video Analysis (YouTube and local files)

Run this script to test the new capabilities.
"""

import asyncio
import base64
from pathlib import Path
from typing import List
import sys
import os

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from integrations.gemini.client import GeminiClient, GeminiConfig


async def demo_bounding_boxes():
    """Demo: Detect objects with bounding boxes."""
    print("\n" + "="*80)
    print("DEMO 1: Bounding Box Object Detection")
    print("="*80)
    
    client = GeminiClient(GeminiConfig())
    
    # Example: Analyze a room image
    # Replace with actual image path
    image_path = "path/to/room_image.jpg"
    
    if not Path(image_path).exists():
        print(f"⚠️  Image not found: {image_path}")
        print("   Please provide a valid room image path to test this feature.")
        return
    
    print(f"\n📸 Analyzing image: {image_path}")
    print("   Detecting: sofa, lamp, table, window, door")
    
    result = await client.analyze_with_bounding_boxes(
        image=image_path,
        objects_to_detect=["sofa", "lamp", "table", "window", "door"],
        room_hint="living room"
    )
    
    print(f"\n✅ Detected {len(result.get('objects', []))} objects:")
    for obj in result.get('objects', [])[:5]:  # Show first 5
        label = obj.get('label', 'Unknown')
        confidence = obj.get('confidence', 0)
        bbox = obj.get('bounding_box', {})
        print(f"   • {label} (confidence: {confidence:.2f})")
        print(f"     Box: [{bbox.get('y_min')}, {bbox.get('x_min')}, {bbox.get('y_max')}, {bbox.get('x_max')}]")


async def demo_segmentation():
    """Demo: Segment objects with masks."""
    print("\n" + "="*80)
    print("DEMO 2: Object Segmentation with Masks")
    print("="*80)
    
    client = GeminiClient(GeminiConfig())
    
    image_path = "path/to/room_image.jpg"
    
    if not Path(image_path).exists():
        print(f"⚠️  Image not found: {image_path}")
        print("   Please provide a valid room image path to test this feature.")
        return
    
    print(f"\n📸 Segmenting objects in: {image_path}")
    
    result = await client.analyze_with_segmentation(
        image=image_path,
        objects_to_segment=["sofa", "table"],
        room_hint="living room"
    )
    
    print(f"\n✅ Segmented {len(result.get('segments', []))} objects:")
    for seg in result.get('segments', []):
        label = seg.get('label', 'Unknown')
        has_mask = 'mask' in seg
        print(f"   • {label} (mask: {'✓' if has_mask else '✗'})")


async def demo_multi_image_sequence():
    """Demo: Analyze before/after image sequences."""
    print("\n" + "="*80)
    print("DEMO 3: Multi-Image Sequence Analysis")
    print("="*80)
    
    client = GeminiClient(GeminiConfig())
    
    # Example: Before and after renovation images
    before_image = "path/to/before.jpg"
    after_image = "path/to/after.jpg"
    
    if not Path(before_image).exists() or not Path(after_image).exists():
        print(f"⚠️  Images not found")
        print("   Please provide valid before/after images to test this feature.")
        return
    
    print(f"\n📸 Analyzing sequence:")
    print(f"   Before: {before_image}")
    print(f"   After:  {after_image}")
    
    result = await client.analyze_multi_image_sequence(
        images=[before_image, after_image],
        sequence_type="before_after"
    )
    
    print(f"\n✅ Analysis Results:")
    print(f"   Changes Made: {result.get('changes_made', [])}")
    print(f"   Improvements: {result.get('improvements', [])}")
    print(f"   Cost Range: {result.get('estimated_cost_range', 'N/A')}")
    print(f"   DIY Feasibility: {result.get('diy_feasibility', 'N/A')}")


async def demo_diy_instructions():
    """Demo: Generate structured DIY instructions."""
    print("\n" + "="*80)
    print("DEMO 4: Structured DIY Instructions Generation")
    print("="*80)
    
    client = GeminiClient(GeminiConfig())
    
    project = "Paint a bedroom with accent wall"
    
    print(f"\n🛠️  Generating DIY instructions for: {project}")
    
    result = await client.generate_diy_instructions(
        project_description=project
    )
    
    if 'error' in result:
        print(f"❌ Error: {result['error']}")
        return
    
    print(f"\n✅ DIY Instructions Generated:")
    print(f"   Title: {result.get('title', 'N/A')}")
    print(f"   Difficulty: {result.get('difficulty', 'N/A')}")
    print(f"   Estimated Time: {result.get('estimated_time', 'N/A')}")
    print(f"   Estimated Cost: {result.get('estimated_cost', 'N/A')}")
    
    materials = result.get('materials', [])
    print(f"\n   Materials ({len(materials)}):")
    for mat in materials[:5]:  # Show first 5
        print(f"     • {mat}")
    
    tools = result.get('tools', [])
    print(f"\n   Tools ({len(tools)}):")
    for tool in tools[:5]:
        print(f"     • {tool}")
    
    steps = result.get('steps', [])
    print(f"\n   Steps ({len(steps)}):")
    for i, step in enumerate(steps[:3], 1):  # Show first 3
        print(f"     {i}. {step}")
    
    safety = result.get('safety_tips', [])
    if safety:
        print(f"\n   Safety Tips:")
        for tip in safety[:2]:
            print(f"     ⚠️  {tip}")


async def demo_video_analysis():
    """Demo: Analyze YouTube DIY tutorial."""
    print("\n" + "="*80)
    print("DEMO 5: Video Analysis (YouTube)")
    print("="*80)
    
    client = GeminiClient(GeminiConfig())
    
    # Example YouTube DIY video
    youtube_url = "https://www.youtube.com/watch?v=EXAMPLE"
    
    print(f"\n🎥 Analyzing YouTube video: {youtube_url}")
    print("   Analysis type: tutorial")
    
    # Note: This requires a valid YouTube URL
    print("\n⚠️  This demo requires a valid YouTube URL.")
    print("   Replace 'EXAMPLE' with an actual video ID to test.")
    print("\n   Example usage:")
    print("   ```python")
    print("   result = await client.analyze_youtube_video(")
    print("       youtube_url='https://www.youtube.com/watch?v=dQw4w9WgXcQ',")
    print("       prompt='Extract DIY steps with timestamps'")
    print("   )")
    print("   ```")


async def demo_structured_content():
    """Demo: Generate structured content with custom schema."""
    print("\n" + "="*80)
    print("DEMO 6: Structured Content Generation (Custom Schema)")
    print("="*80)
    
    from typing_extensions import TypedDict
    
    # Define custom schema
    class RoomAnalysis(TypedDict):
        style: str
        color_palette: List[str]
        furniture_list: List[str]
        estimated_value: str
        renovation_priority: str
    
    client = GeminiClient(GeminiConfig())
    
    prompt = """
    Analyze this living room and provide:
    - Overall style (modern, traditional, etc.)
    - Color palette (list of main colors)
    - Furniture list
    - Estimated room value range
    - Renovation priority (low/medium/high)
    """
    
    print(f"\n📝 Generating structured analysis with custom schema")
    print("   Schema: RoomAnalysis (style, color_palette, furniture_list, ...)")
    
    # Note: Requires an image
    print("\n⚠️  This demo requires an image input.")
    print("   Example usage:")
    print("   ```python")
    print("   result = await client.generate_structured_content(")
    print("       prompt=prompt,")
    print("       image='path/to/room.jpg',")
    print("       response_schema=RoomAnalysis")
    print("   )")
    print("   ```")


async def main():
    """Run all demos."""
    print("\n" + "="*80)
    print("🏠 HomeView AI - Gemini Cookbook Features Demo")
    print("="*80)
    print("\nThis script demonstrates the new AI capabilities:")
    print("  1. Bounding Box Object Detection")
    print("  2. Object Segmentation with Masks")
    print("  3. Multi-Image Sequence Analysis")
    print("  4. Structured DIY Instructions")
    print("  5. Video Analysis (YouTube)")
    print("  6. Custom Structured Content")
    
    # Run demos
    await demo_bounding_boxes()
    await demo_segmentation()
    await demo_multi_image_sequence()
    await demo_diy_instructions()
    await demo_video_analysis()
    await demo_structured_content()
    
    print("\n" + "="*80)
    print("✅ Demo Complete!")
    print("="*80)
    print("\nNext Steps:")
    print("  1. Replace placeholder image paths with actual test images")
    print("  2. Add a valid YouTube URL for video analysis")
    print("  3. Integrate these features into the Design Studio UI")
    print("  4. Add frontend components for displaying results")
    print("\nSee GEMINI_COOKBOOK_IMPLEMENTATION.md for full documentation.")
    print("="*80 + "\n")


if __name__ == "__main__":
    asyncio.run(main())

