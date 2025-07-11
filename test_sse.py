#!/usr/bin/env python3
"""
Test script for SSE endpoint
"""
import asyncio
import httpx
import json

async def test_sse_endpoint():
    """Test the SSE endpoint and display the streaming data"""
    url = "http://localhost:8003/api/v1/mcp/sse"
    
    try:
        async with httpx.AsyncClient() as client:
            print(f"Connecting to {url}")
            print("=" * 50)
            
            counter = 0
            async with client.stream("GET", url) as response:
                print(f"Response status: {response.status_code}")
                print(f"Headers: {dict(response.headers)}")
                print("=" * 50)
                print("Streaming data:")
                print()
                
                async for chunk in response.aiter_text():
                    if chunk.strip():
                        print(f"Event {counter + 1}:")
                        print(chunk)
                        print("-" * 30)
                        counter += 1
                        
                        # Stop after 3 events for demonstration
                        if counter >= 3:
                            break
                            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_sse_endpoint())