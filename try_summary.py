#!/usr/bin/env python3
"""
Test script to try the health summary endpoint with different parameters.
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

async def test_summary_endpoint():
    """Test the health summary endpoint with various parameters."""
    headers = {"X-API-Key": API_KEY}
    
    # Try with different period values
    periods = ["day", "week", "month", "year"]
    
    for period in periods:
        print(f"\n--- Testing /health/summary/{period} ---")
        
        # Try with default parameters
        print(f"\nDefault parameters:")
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{API_BASE_URL}/health/summary/{period}", 
                    headers=headers
                )
                
                print(f"Status: {response.status_code}")
                if response.status_code == 200:
                    data = response.json()
                    print(f"Success - got {type(data)} with keys: {list(data.keys())}")
                    if "summaries" in data:
                        print(f"Number of summaries: {len(data['summaries'])}")
                else:
                    print(f"Error: {response.text}")
        except Exception as e:
            print(f"Request failed: {str(e)}")
        
        # Try with span=1
        print(f"\nWith span=1:")
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{API_BASE_URL}/health/summary/{period}", 
                    headers=headers,
                    params={"span": 1}
                )
                
                print(f"Status: {response.status_code}")
                if response.status_code == 200:
                    data = response.json()
                    print(f"Success - got {type(data)} with keys: {list(data.keys())}")
                    if "summaries" in data:
                        print(f"Number of summaries: {len(data['summaries'])}")
                else:
                    print(f"Error: {response.text}")
        except Exception as e:
            print(f"Request failed: {str(e)}")
        
        # Try with metrics=steps,calories
        print(f"\nWith metrics=steps,calories:")
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{API_BASE_URL}/health/summary/{period}", 
                    headers=headers,
                    params={"metrics": "steps,calories"}
                )
                
                print(f"Status: {response.status_code}")
                if response.status_code == 200:
                    data = response.json()
                    print(f"Success - got {type(data)} with keys: {list(data.keys())}")
                    if "summaries" in data:
                        print(f"Number of summaries: {len(data['summaries'])}")
                        if len(data["summaries"]) > 0:
                            print(f"Metrics in first summary: {list(data['summaries'][0]['metrics'].keys())}")
                else:
                    print(f"Error: {response.text}")
        except Exception as e:
            print(f"Request failed: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test_summary_endpoint())