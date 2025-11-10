"""
Test script for chat image generation functionality.
"""

import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from backend.workflows.chat_workflow import ChatWorkflow
from backend.models.base import get_async_db
from sqlalchemy.ext.asyncio import AsyncSession


async def test_image_generation():
    """Test image generation in chat workflow."""
    
    print("=" * 60)
    print("Testing Chat Image Generation")
    print("=" * 60)
    
    # Get database session
    async for db in get_async_db():
        try:
            # Initialize workflow
            workflow = ChatWorkflow(db)
            
            # Test 1: Text-only design visualization
            print("\n[Test 1] Text-only design visualization")
            print("-" * 60)
            
            test_input_1 = {
                "user_message": "Show me modern bathroom designs with white tiles",
                "conversation_id": "test-conv-001",
                "user_id": "550e8400-e29b-41d4-a716-446655440000",
                "home_id": "",
                "context": {},
                "persona": "homeowner",
                "scenario": None,
                "mode": "agent",
                "uploaded_image_path": None,
            }
            
            print(f"Input: {test_input_1['user_message']}")
            print("Executing workflow...")
            
            result_1 = await workflow.execute(test_input_1)
            
            print(f"\nIntent: {result_1.get('intent')}")
            print(f"Status: {result_1.get('status')}")
            
            generated_images = result_1.get('generated_images', [])
            print(f"\nGenerated Images: {len(generated_images)}")
            
            for i, img in enumerate(generated_images, 1):
                print(f"  {i}. Type: {img.get('type')}, Caption: {img.get('caption')}")
                print(f"     URL: {img.get('url')}")
            
            # Test 2: Style extraction
            print("\n\n[Test 2] Style extraction")
            print("-" * 60)
            
            test_messages = [
                "I want a modern minimalist kitchen",
                "Show me rustic farmhouse bedroom ideas",
                "Create a scandinavian living room design",
                "I love industrial loft style bathrooms",
            ]
            
            for msg in test_messages:
                style = workflow._extract_style_from_message(msg)
                print(f"Message: '{msg}'")
                print(f"  → Extracted style: {style}\n")
            
            # Test 3: Prompt building
            print("\n[Test 3] Image generation prompt building")
            print("-" * 60)
            
            user_msg = "I want to refresh my small bathroom with a modern look, budget is $800"
            ai_response = "Great! I can help you with that."
            
            prompt = workflow._build_image_generation_prompt(user_msg, ai_response)
            print(f"User message: {user_msg}")
            print(f"\nGenerated prompt:\n{prompt}")
            
            print("\n" + "=" * 60)
            print("✅ Tests completed!")
            print("=" * 60)
            
        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()
        finally:
            break


if __name__ == "__main__":
    asyncio.run(test_image_generation())

