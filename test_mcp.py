#!/usr/bin/env python3
"""
Test script to compare MCP responses with direct API responses.
"""
import asyncio
import json
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def test_mcp_api():
    """Test MCP API calls to validate endpoints."""
    # Create parameters for connecting to the server
    server_params = StdioServerParameters(
        command="python",
        args=["senechal_mcp_server.py"],
        env=None  # Use environment variables from the current process
    )
    
    # Connect to the server using the stdio transport
    async with stdio_client(server_params) as (read, write):
        # Create a client session
        async with ClientSession(read, write) as session:
            # Initialize the connection
            print("Initializing connection to Senechal MCP server...")
            await session.initialize()
            
            # Test health profile tool
            print("\nTesting fetch_health_profile tool...")
            try:
                result = await session.call_tool("fetch_health_profile", arguments={})
                if hasattr(result, 'content') and result.content:
                    for content_item in result.content:
                        if hasattr(content_item, 'text'):
                            try:
                                data = json.loads(content_item.text)
                                print(f"  Data type: {type(data)}")
                                print(f"  Keys: {list(data.keys())}")
                                print(f"  Demographics: {data.get('demographics', {})}")
                            except:
                                print(f"  Error parsing JSON: {content_item.text}")
                else:
                    print(f"  Result: {result}")
            except Exception as e:
                print(f"  Error: {e}")
            
            # Test health summary tool
            print("\nTesting fetch_health_summary tool...")
            try:
                result = await session.call_tool(
                    "fetch_health_summary", 
                    arguments={
                        "period": "day",
                        "metrics": "all",
                        "span": 2,
                        "offset": 0
                    }
                )
                if hasattr(result, 'content') and result.content:
                    for content_item in result.content:
                        if hasattr(content_item, 'text'):
                            try:
                                data = json.loads(content_item.text)
                                print(f"  Data type: {type(data)}")
                                print(f"  Keys: {list(data.keys())}")
                                if "error" in data:
                                    print(f"  Error from API: {data['error']}")
                                elif "summaries" in data:
                                    print(f"  Number of summaries: {len(data['summaries'])}")
                            except:
                                print(f"  Error parsing JSON: {content_item.text}")
                else:
                    print(f"  Result: {result}")
            except Exception as e:
                print(f"  Error: {e}")
            
            # Test current health tool
            print("\nTesting fetch_current_health tool...")
            try:
                result = await session.call_tool("fetch_current_health", arguments={})
                if hasattr(result, 'content') and result.content:
                    for content_item in result.content:
                        if hasattr(content_item, 'text'):
                            try:
                                data = json.loads(content_item.text)
                                print(f"  Data type: {type(data)}")
                                print(f"  Keys: {list(data.keys())}")
                                if "measurements" in data:
                                    print(f"  Number of measurements: {len(data['measurements'])}")
                            except:
                                print(f"  Error parsing JSON: {content_item.text}")
                else:
                    print(f"  Result: {result}")
            except Exception as e:
                print(f"  Error: {e}")
            
            # Test trends tool
            print("\nTesting fetch_health_trends tool...")
            try:
                result = await session.call_tool(
                    "fetch_health_trends", 
                    arguments={
                        "days": 7,
                        "interval": "day"
                    }
                )
                if hasattr(result, 'content') and result.content:
                    for content_item in result.content:
                        if hasattr(content_item, 'text'):
                            try:
                                data = json.loads(content_item.text)
                                print(f"  Data type: {type(data)}")
                                print(f"  Keys: {list(data.keys())}")
                                if "trends" in data:
                                    print(f"  Number of trend categories: {len(data['trends'])}")
                            except:
                                print(f"  Error parsing JSON: {content_item.text}")
                else:
                    print(f"  Result: {result}")
            except Exception as e:
                print(f"  Error: {e}")
            
            # Test stats tool
            print("\nTesting fetch_health_stats tool...")
            try:
                result = await session.call_tool(
                    "fetch_health_stats", 
                    arguments={
                        "days": 30
                    }
                )
                if hasattr(result, 'content') and result.content:
                    for content_item in result.content:
                        if hasattr(content_item, 'text'):
                            try:
                                data = json.loads(content_item.text)
                                print(f"  Data type: {type(data)}")
                                print(f"  Keys: {list(data.keys())}")
                                if "stats" in data:
                                    print(f"  Number of stat metrics: {len(data['stats'])}")
                            except:
                                print(f"  Error parsing JSON: {content_item.text}")
                else:
                    print(f"  Result: {result}")
            except Exception as e:
                print(f"  Error: {e}")
            
            # Test prompts
            print("\nTesting analyze_health_summary prompt...")
            try:
                prompt_result = await session.get_prompt("analyze_health_summary")
                print("  Prompt available: Yes")
                for message in prompt_result.messages:
                    print(f"  Message role: {message.role}")
            except Exception as e:
                print(f"  Error: {e}")
                
            print("\nTesting compare_health_trends prompt...")
            try:
                prompt_result = await session.get_prompt("compare_health_trends")
                print("  Prompt available: Yes")
                for message in prompt_result.messages:
                    print(f"  Message role: {message.role}")
            except Exception as e:
                print(f"  Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_mcp_api())