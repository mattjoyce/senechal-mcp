#!/usr/bin/env python3
"""
Example client for the Senechal MCP server.
This demonstrates basic usage of the MCP client to interact with the server.
"""
import asyncio
import json
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def main():
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
            
            # List available resources
            print("\nAvailable Resources:")
            resources = await session.list_resources()
            # Check if resources is a list/tuple or has a different structure
            if hasattr(resources, 'resources'):
                # API returned an object with a resources property
                for resource in resources.resources:
                    print(f"- {resource.uri}: {getattr(resource, 'description', 'No description')}")
            else:
                # API returned resources directly
                for resource in resources:
                    if isinstance(resource, tuple):
                        # If resources are tuples, they might be (uri, name, description)
                        if len(resource) >= 3:
                            print(f"- {resource[0]}: {resource[2]}")
                        else:
                            print(f"- {resource[0]}")
                    elif hasattr(resource, 'uri'):
                        # If resources are objects with properties
                        print(f"- {resource.uri}: {getattr(resource, 'description', 'No description')}")
                    else:
                        # Fallback
                        print(f"- {resource}")
            
            # List available tools
            print("\nAvailable Tools:")
            tools = await session.list_tools()
            # Adapt for possible different return formats
            if hasattr(tools, 'tools'):
                for tool in tools.tools:
                    print(f"- {tool.name}: {getattr(tool, 'description', 'No description')}")
            else:
                for tool in tools:
                    if isinstance(tool, tuple):
                        if len(tool) >= 2:
                            print(f"- {tool[0]}: {tool[1] if len(tool) > 1 else 'No description'}")
                        else:
                            print(f"- {tool[0]}")
                    elif hasattr(tool, 'name'):
                        print(f"- {tool.name}: {getattr(tool, 'description', 'No description')}")
                    else:
                        print(f"- {tool}")
            
            # List available prompts
            print("\nAvailable Prompts:")
            try:
                prompts = await session.list_prompts()
                # Adapt for possible different return formats
                if hasattr(prompts, 'prompts'):
                    for prompt in prompts.prompts:
                        print(f"- {prompt.name}: {getattr(prompt, 'description', 'No description')}")
                else:
                    for prompt in prompts:
                        if isinstance(prompt, tuple):
                            if len(prompt) >= 2:
                                print(f"- {prompt[0]}: {prompt[1] if len(prompt) > 1 else 'No description'}")
                            else:
                                print(f"- {prompt[0]}")
                        elif hasattr(prompt, 'name'):
                            print(f"- {prompt.name}: {getattr(prompt, 'description', 'No description')}")
                        else:
                            print(f"- {prompt}")
            except Exception as e:
                print(f"Error listing prompts: {e}")
            
            # Read a resource
            try:
                print("\nFetching health summary for day:")
                result = await session.read_resource("senechal://health/summary/day?span=2&metrics=all")
                print("Resource result type:", type(result).__name__)
                
                # Handle different response formats
                if isinstance(result, dict):
                    # Direct dictionary response
                    print(json.dumps(result, indent=2))
                elif isinstance(result, str):
                    # String response, try to parse as JSON if it looks like JSON
                    if result.strip().startswith('{') or result.strip().startswith('['):
                        try:
                            data = json.loads(result)
                            print(json.dumps(data, indent=2))
                        except json.JSONDecodeError:
                            print(result)
                    else:
                        print(result)
                elif hasattr(result, 'resource_contents'):
                    # Handle resource_contents attribute
                    print("Resource contents:", result.resource_contents)
                    print(json.dumps(result.resource_contents, indent=2))
                elif hasattr(result, 'contents'):
                    # Handle contents attribute
                    if isinstance(result.contents, list) and len(result.contents) > 0:
                        for content_item in result.contents:
                            if hasattr(content_item, 'text'):
                                try:
                                    # Try to parse as JSON
                                    json_data = json.loads(content_item.text)
                                    print(json.dumps(json_data, indent=2))
                                except json.JSONDecodeError:
                                    print(f"Content text: {content_item.text}")
                            else:
                                print(f"Content item: {content_item}")
                    else:
                        print(f"Contents: {result.contents}")
                        
                # Special handling for ReadResourceResult type
                if hasattr(result, '__class__') and result.__class__.__name__ == 'ReadResourceResult':
                    if hasattr(result, 'contents'):
                        content_items = result.contents
                        if isinstance(content_items, list) and len(content_items) > 0:
                            for item in content_items:
                                if hasattr(item, 'text'):
                                    try:
                                        json_data = json.loads(item.text)
                                        print("Parsed ReadResourceResult contents:")
                                        print(json.dumps(json_data, indent=2))
                                    except (json.JSONDecodeError, TypeError):
                                        pass
                else:
                    # Fall back to string representation
                    print(result)
                    
            except Exception as e:
                print(f"Error reading resource: {e}")
                import traceback
                traceback.print_exc()
            
            # Call a tool
            try:
                print("\nCalling fetch_health_profile tool:")
                result = await session.call_tool("fetch_health_profile", arguments={})
                print("Tool result type:", type(result).__name__)
                
                # Extract the result data based on the structure
                if hasattr(result, 'result'):
                    print("Result has 'result' attribute")
                    result_data = result.result
                elif hasattr(result, 'return_value'):
                    print("Result has 'return_value' attribute")
                    result_data = result.return_value
                else:
                    print("Using result directly")
                    result_data = result
                
                if isinstance(result_data, dict):
                    print(json.dumps(result_data, indent=2))
                elif isinstance(result_data, str):
                    try:
                        json_data = json.loads(result_data)
                        print(json.dumps(json_data, indent=2))
                    except json.JSONDecodeError:
                        print(result_data)
                elif hasattr(result_data, 'content') and isinstance(result_data.content, list):
                    # Extract content from result_data.content list
                    for content_item in result_data.content:
                        if hasattr(content_item, 'text'):
                            try:
                                json_data = json.loads(content_item.text)
                                print(json.dumps(json_data, indent=2))
                            except json.JSONDecodeError:
                                print(content_item.text)
                        else:
                            print(content_item)
                else:
                    print(f"Result data (type {type(result_data).__name__}):", result_data)
            except Exception as e:
                print(f"Error calling tool: {e}")
                import traceback
                traceback.print_exc()
            
            # Get a prompt
            try:
                print("\nGetting analyze_health_summary prompt:")
                prompt_result = await session.get_prompt("analyze_health_summary")
                print("Prompt:")
                for message in prompt_result.messages:
                    print(f"[{message.role}]: {message.content.text}")
            except Exception as e:
                print(f"Error getting prompt: {e}")

if __name__ == "__main__":
    asyncio.run(main())