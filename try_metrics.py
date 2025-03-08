#!/usr/bin/env python3
"""
Test script to try the available metrics endpoint.
"""
import asyncio
import httpx
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

async def test_metrics_endpoint():
    """Test the available metrics endpoint."""
    headers = {"X-API-Key": API_KEY}
    
    print(f"\n--- Testing /health/availablemetrics ---")
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{API_BASE_URL}/health/availablemetrics", 
                headers=headers
            )
            
            print(f"Status: {response.status_code}")
            if response.status_code == 200:
                # This should return text, not JSON
                data = response.text
                print(f"Success - got text of length: {len(data)}")
                # Print the first 200 characters as a preview
                print(f"Preview: {data[:200]}...")
            else:
                print(f"Error: {response.text}")
    except Exception as e:
        print(f"Request failed: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test_metrics_endpoint())