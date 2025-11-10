"""
Test script for multimodal chat features.

Tests:
1. YouTube search integration
2. Chat workflow with multimodal enrichment
3. Mode switching (chat vs agent)
"""

import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from backend.integrations.youtube_search import YouTubeSearchClient
from backend.workflows.chat_workflow import ChatWorkflow
from backend.integrations.gemini.client import GeminiClient
from backend.core.orchestrator import WorkflowOrchestrator


async def test_youtube_search():
    """Test YouTube search integration."""
    print("\n" + "="*60)
    print("TEST 1: YouTube Search Integration")
    print("="*60)
    
    youtube = YouTubeSearchClient()
    
    # Test 1: Search for tutorials
    print("\n📺 Searching for 'how to install bathroom exhaust fan'...")
    videos = await youtube.search_tutorials(
        query="how to install bathroom exhaust fan",
        max_results=3,
    )
    
    print(f"\n✅ Found {len(videos)} videos:")
    for i, video in enumerate(videos, 1):
        print(f"\n{i}. {video['title']}")
        print(f"   Channel: {video['channel']}")
        print(f"   Duration: {video.get('duration', 'N/A')}")
        print(f"   URL: {video['url']}")
        print(f"   Trusted: {'✓' if video.get('is_trusted_channel') else '✗'}")
    
    # Test 2: Search for task
    print("\n📺 Searching for task: 'Install exhaust fan' in bathroom...")
    videos = await youtube.search_for_task(
        task_description="Install exhaust fan",
        room_type="bathroom",
        max_results=2
    )
    
    print(f"\n✅ Found {len(videos)} videos:")
    for i, video in enumerate(videos, 1):
        print(f"\n{i}. {video['title']}")
        print(f"   Channel: {video['channel']}")
    
    return True


async def test_chat_workflow_agent_mode():
    """Test chat workflow with Agent mode (multimodal features enabled)."""
    print("\n" + "="*60)
    print("TEST 2: Chat Workflow - Agent Mode")
    print("="*60)
    
    # Initialize workflow
    gemini_client = GeminiClient()
    orchestrator = WorkflowOrchestrator(workflow_name="chat_workflow")
    workflow = ChatWorkflow(orchestrator, gemini_client)
    
    # Test with DIY question (should trigger YouTube videos)
    print("\n🤖 Testing Agent mode with DIY question...")
    print("Question: 'How do I install a bathroom exhaust fan?'")
    
    result = await workflow.execute({
        "user_message": "How do I install a bathroom exhaust fan?",
        "mode": "agent",  # Agent mode - multimodal features enabled
        "persona": "diy_worker",
        "conversation_history": []
    })
    
    print(f"\n✅ Workflow Status: {result.get('status')}")
    print(f"✅ Intent: {result.get('intent')}")
    
    # Check for multimodal content
    response_metadata = result.get("response_metadata", {})
    
    if response_metadata.get("youtube_videos"):
        videos = response_metadata["youtube_videos"]
        print(f"\n📺 YouTube Videos: {len(videos)} found")
        for i, video in enumerate(videos[:2], 1):
            print(f"   {i}. {video['title']}")
    else:
        print("\n⚠️  No YouTube videos found (expected for DIY intent)")
    
    if response_metadata.get("web_search_results"):
        products = response_metadata["web_search_results"]
        print(f"\n🔍 Web Search Results: {len(products)} found")
    else:
        print("\n✓ No web search results (expected for DIY intent)")
    
    return True


async def test_chat_workflow_chat_mode():
    """Test chat workflow with Chat mode (multimodal features disabled)."""
    print("\n" + "="*60)
    print("TEST 3: Chat Workflow - Chat Mode")
    print("="*60)
    
    # Initialize workflow
    gemini_client = GeminiClient()
    orchestrator = WorkflowOrchestrator(workflow_name="chat_workflow")
    workflow = ChatWorkflow(orchestrator, gemini_client)
    
    # Test with same question in Chat mode
    print("\n💬 Testing Chat mode with same question...")
    print("Question: 'How do I install a bathroom exhaust fan?'")
    
    result = await workflow.execute({
        "user_message": "How do I install a bathroom exhaust fan?",
        "mode": "chat",  # Chat mode - multimodal features disabled
        "persona": "diy_worker",
        "conversation_history": []
    })
    
    print(f"\n✅ Workflow Status: {result.get('status')}")
    print(f"✅ Intent: {result.get('intent')}")
    
    # Check that multimodal content is NOT present
    response_metadata = result.get("response_metadata", {})
    
    has_youtube = bool(response_metadata.get("youtube_videos"))
    has_web_search = bool(response_metadata.get("web_search_results"))
    
    if not has_youtube and not has_web_search:
        print("\n✅ Chat mode working correctly: No multimodal content")
    else:
        print("\n⚠️  Warning: Chat mode should not have multimodal content")
        if has_youtube:
            print(f"   - Found {len(response_metadata['youtube_videos'])} YouTube videos")
        if has_web_search:
            print(f"   - Found {len(response_metadata['web_search_results'])} web results")
    
    return True


async def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("🧪 MULTIMODAL CHAT FEATURES TEST SUITE")
    print("="*60)
    
    try:
        # Test 1: YouTube Search
        await test_youtube_search()
        
        # Test 2: Agent Mode (multimodal enabled)
        await test_chat_workflow_agent_mode()
        
        # Test 3: Chat Mode (multimodal disabled)
        await test_chat_workflow_chat_mode()
        
        print("\n" + "="*60)
        print("✅ ALL TESTS COMPLETED!")
        print("="*60)
        print("\nNext steps:")
        print("1. Start the frontend: cd homeview-frontend && npm run dev")
        print("2. Go to http://localhost:3000/")
        print("3. Toggle between Chat and Agent modes")
        print("4. Ask: 'How do I install a bathroom exhaust fan?'")
        print("5. Verify YouTube videos appear in Agent mode")
        print("6. Verify no videos appear in Chat mode")
        print("\n")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


if __name__ == "__main__":
    asyncio.run(main())

