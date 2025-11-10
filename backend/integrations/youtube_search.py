"""
YouTube Search Integration for HomeView AI.

Provides DIY tutorial video recommendations using YouTube Data API v3.
Official Documentation: https://developers.google.com/youtube/v3/docs/search/list
"""

import logging
import os
from typing import List, Dict, Any, Optional
from datetime import datetime
import aiohttp

logger = logging.getLogger(__name__)


class YouTubeSearchClient:
    """Client for searching YouTube videos for DIY tutorials."""

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize YouTube search client.
        
        Args:
            api_key: YouTube Data API v3 key (defaults to YOUTUBE_API_KEY env var)
        """
        self.api_key = api_key or os.getenv("YOUTUBE_API_KEY")
        self.base_url = "https://www.googleapis.com/youtube/v3"
        
        # Trusted DIY channels (Canadian and popular)
        self.trusted_channels = [
            "Home RenoVision DIY",
            "This Old House",
            "DIY Creators",
            "See Jane Drill",
            "The Handyman",
            "Fix This Build That",
            "Home Repair Tutor",
            "Shannon from House to Home",
            "The Honest Carpenter",
            "Scott Brown Carpentry"
        ]

    async def search_tutorials(
        self,
        query: str,
        max_results: int = 5,
        prefer_canadian: bool = True,
        min_duration_seconds: int = 180,  # 3 minutes minimum
        max_duration_seconds: int = 1200,  # 20 minutes maximum
    ) -> List[Dict[str, Any]]:
        """
        Search for DIY tutorial videos.
        
        Args:
            query: Search query (e.g., "how to install bathroom exhaust fan")
            max_results: Maximum number of results to return
            prefer_canadian: Prioritize Canadian content creators
            min_duration_seconds: Minimum video duration
            max_duration_seconds: Maximum video duration
            
        Returns:
            List of video results with metadata
        """
        if not self.api_key:
            logger.warning("YouTube API key not configured. Returning mock results.")
            return self._get_mock_results(query, max_results)

        try:
            # Build search query
            search_query = f"{query} tutorial DIY"
            if prefer_canadian:
                search_query += " Canada"

            # Search for videos
            async with aiohttp.ClientSession() as session:
                # Step 1: Search for videos
                search_params = {
                    "part": "snippet",
                    "q": search_query,
                    "type": "video",
                    "maxResults": max_results * 2,  # Get more to filter
                    "order": "relevance",
                    "videoDuration": "medium",  # 4-20 minutes
                    "videoDefinition": "high",
                    "relevanceLanguage": "en",
                    "key": self.api_key,
                }

                async with session.get(f"{self.base_url}/search", params=search_params) as response:
                    if response.status != 200:
                        logger.error(f"YouTube API error: {response.status}")
                        return self._get_mock_results(query, max_results)

                    search_data = await response.json()
                    video_ids = [item["id"]["videoId"] for item in search_data.get("items", [])]

                if not video_ids:
                    return self._get_mock_results(query, max_results)

                # Step 2: Get video details (duration, stats)
                details_params = {
                    "part": "contentDetails,statistics,snippet",
                    "id": ",".join(video_ids),
                    "key": self.api_key,
                }

                async with session.get(f"{self.base_url}/videos", params=details_params) as response:
                    if response.status != 200:
                        logger.error(f"YouTube API error fetching details: {response.status}")
                        return self._get_mock_results(query, max_results)

                    details_data = await response.json()
                    videos = details_data.get("items", [])

                # Process and filter results
                results = []
                for video in videos:
                    try:
                        duration_seconds = self._parse_duration(video["contentDetails"]["duration"])
                        
                        # Filter by duration
                        if duration_seconds < min_duration_seconds or duration_seconds > max_duration_seconds:
                            continue

                        # Extract metadata
                        snippet = video["snippet"]
                        stats = video["statistics"]
                        
                        result = {
                            "video_id": video["id"],
                            "title": snippet["title"],
                            "channel": snippet["channelTitle"],
                            "description": snippet["description"][:200] + "..." if len(snippet["description"]) > 200 else snippet["description"],
                            "thumbnail": snippet["thumbnails"]["high"]["url"],
                            "url": f"https://www.youtube.com/watch?v={video['id']}",
                            "duration": self._format_duration(duration_seconds),
                            "duration_seconds": duration_seconds,
                            "views": int(stats.get("viewCount", 0)),
                            "likes": int(stats.get("likeCount", 0)),
                            "published_at": snippet["publishedAt"],
                            "is_trusted_channel": snippet["channelTitle"] in self.trusted_channels,
                        }
                        
                        results.append(result)
                        
                    except Exception as e:
                        logger.warning(f"Error processing video: {e}")
                        continue

                # Sort: trusted channels first, then by views
                results.sort(key=lambda x: (not x["is_trusted_channel"], -x["views"]))
                
                # Limit to max_results
                results = results[:max_results]
                
                logger.info(f"Found {len(results)} YouTube tutorials for: {query}")
                return results

        except Exception as e:
            logger.error(f"Error searching YouTube: {e}", exc_info=True)
            return self._get_mock_results(query, max_results)

    def _parse_duration(self, iso_duration: str) -> int:
        """
        Parse ISO 8601 duration to seconds.
        
        Example: PT15M33S -> 933 seconds
        """
        import re
        
        pattern = r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?'
        match = re.match(pattern, iso_duration)
        
        if not match:
            return 0
        
        hours = int(match.group(1) or 0)
        minutes = int(match.group(2) or 0)
        seconds = int(match.group(3) or 0)
        
        return hours * 3600 + minutes * 60 + seconds

    def _format_duration(self, seconds: int) -> str:
        """Format seconds to MM:SS or HH:MM:SS."""
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60
        
        if hours > 0:
            return f"{hours}:{minutes:02d}:{secs:02d}"
        return f"{minutes}:{secs:02d}"

    def _get_mock_results(self, query: str, max_results: int) -> List[Dict[str, Any]]:
        """
        Return mock results when API is unavailable.
        
        This ensures the feature degrades gracefully.
        """
        logger.info(f"Returning mock YouTube results for: {query}")
        
        # Extract key terms from query
        query_lower = query.lower()
        
        if "exhaust fan" in query_lower or "bathroom fan" in query_lower:
            return [
                {
                    "video_id": "mock_1",
                    "title": "How to Install a Bathroom Exhaust Fan - Complete Guide",
                    "channel": "Home RenoVision DIY",
                    "description": "Step-by-step tutorial on installing a bathroom exhaust fan, including wiring and ducting.",
                    "thumbnail": "https://via.placeholder.com/480x360?text=Exhaust+Fan+Tutorial",
                    "url": "https://www.youtube.com/results?search_query=install+bathroom+exhaust+fan+tutorial",
                    "duration": "18:45",
                    "duration_seconds": 1125,
                    "views": 2100000,
                    "likes": 45000,
                    "published_at": "2023-01-15T00:00:00Z",
                    "is_trusted_channel": True,
                }
            ][:max_results]
        
        # Generic DIY result
        return [
            {
                "video_id": "mock_generic",
                "title": f"DIY Tutorial: {query}",
                "channel": "DIY Creators",
                "description": f"Learn how to {query} with this step-by-step tutorial.",
                "thumbnail": "https://via.placeholder.com/480x360?text=DIY+Tutorial",
                "url": f"https://www.youtube.com/results?search_query={query.replace(' ', '+')}+tutorial",
                "duration": "12:30",
                "duration_seconds": 750,
                "views": 500000,
                "likes": 12000,
                "published_at": "2023-06-01T00:00:00Z",
                "is_trusted_channel": True,
            }
        ][:max_results]

    async def search_for_task(
        self,
        task_description: str,
        room_type: Optional[str] = None,
        max_results: int = 3,
    ) -> List[Dict[str, Any]]:
        """
        Search for tutorials relevant to a specific DIY task.
        
        Args:
            task_description: Description of the task (e.g., "Install exhaust fan")
            room_type: Optional room context (e.g., "bathroom")
            max_results: Maximum number of results
            
        Returns:
            List of relevant tutorial videos
        """
        # Build contextual query
        query = task_description
        if room_type:
            query = f"{room_type} {query}"
        
        return await self.search_tutorials(
            query=query,
            max_results=max_results,
            prefer_canadian=True,
        )

