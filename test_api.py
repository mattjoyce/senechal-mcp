#!/usr/bin/env python3
"""
Test script to compare direct API responses with MCP responses.
"""
import asyncio
import httpx
import json
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

API_BASE_URL = os.getenv("SENECHAL_API_BASE_URL")
API_KEY = os.getenv("SENECHAL_API_KEY")

if not API_BASE_URL:
    raise ValueError("SENECHAL_API_BASE_URL environment variable is required. Please set it in .env file.")

if not API_KEY:
    raise ValueError("SENECHAL_API_KEY environment variable is required. Please set it in .env file.")

async def test_direct_api():
    """Test direct API calls to validate endpoints."""
    headers = {"X-API-Key": API_KEY}
    
    async with httpx.AsyncClient() as client:
        # Test health profile endpoint
        print("Testing /health/profile endpoint...")
        response = await client.get(f"{API_BASE_URL}/health/profile", headers=headers)
        if response.status_code == 200:
            print("  Status: OK")
            profile_data = response.json()
            print(f"  Data type: {type(profile_data)}")
            print(f"  Keys: {list(profile_data.keys())}")
            print(f"  Demographics: {profile_data.get('demographics', {})}")
        else:
            print(f"  Error: Status {response.status_code}")
            print(f"  Response: {response.text}")
        
        # Test health summary endpoint
        print("\nTesting /health/summary/day endpoint...")
        response = await client.get(
            f"{API_BASE_URL}/health/summary/day", 
            headers=headers,
            params={"span": 2, "metrics": "all"}
        )
        if response.status_code == 200:
            print("  Status: OK")
            summary_data = response.json()
            print(f"  Data type: {type(summary_data)}")
            print(f"  Keys: {list(summary_data.keys())}")
            if "summaries" in summary_data:
                print(f"  Number of summaries: {len(summary_data['summaries'])}")
        else:
            print(f"  Error: Status {response.status_code}")
            print(f"  Response: {response.text}")
        
        # Test current health endpoint
        print("\nTesting /health/current endpoint...")
        response = await client.get(f"{API_BASE_URL}/health/current", headers=headers)
        if response.status_code == 200:
            print("  Status: OK")
            current_data = response.json()
            print(f"  Data type: {type(current_data)}")
            print(f"  Keys: {list(current_data.keys())}")
            if "measurements" in current_data:
                print(f"  Number of measurements: {len(current_data['measurements'])}")
        else:
            print(f"  Error: Status {response.status_code}")
            print(f"  Response: {response.text}")
        
        # Test trends endpoint
        print("\nTesting /health/trends endpoint...")
        response = await client.get(
            f"{API_BASE_URL}/health/trends", 
            headers=headers,
            params={"days": 7, "interval": "day"}
        )
        if response.status_code == 200:
            print("  Status: OK")
            trends_data = response.json()
            print(f"  Data type: {type(trends_data)}")
            print(f"  Keys: {list(trends_data.keys())}")
            if "trends" in trends_data:
                print(f"  Number of trend categories: {len(trends_data['trends'])}")
        else:
            print(f"  Error: Status {response.status_code}")
            print(f"  Response: {response.text}")
        
        # Test stats endpoint
        print("\nTesting /health/stats endpoint...")
        response = await client.get(
            f"{API_BASE_URL}/health/stats", 
            headers=headers,
            params={"days": 30}
        )
        if response.status_code == 200:
            print("  Status: OK")
            stats_data = response.json()
            print(f"  Data type: {type(stats_data)}")
            print(f"  Keys: {list(stats_data.keys())}")
            if "stats" in stats_data:
                print(f"  Number of stat metrics: {len(stats_data['stats'])}")
        else:
            print(f"  Error: Status {response.status_code}")
            print(f"  Response: {response.text}")

if __name__ == "__main__":
    asyncio.run(test_direct_api())