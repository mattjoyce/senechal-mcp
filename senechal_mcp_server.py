#!/usr/bin/env python3
from mcp.server.fastmcp import FastMCP, Context
import httpx
import os
import logging
from datetime import datetime
from dotenv import load_dotenv
from typing import Optional, Dict, Any, List
import json
from dataclasses import dataclass

# Set up logging
log_dir = os.path.dirname(os.path.abspath(__file__))
log_file = os.path.join(log_dir, "senechal_mcp_server.log")
logging.basicConfig(
    filename=log_file,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger("senechal_mcp")

# Create stats tracking
class ServerStats:
    def __init__(self):
        self.api_calls = 0
        self.resource_requests = 0
        self.tool_calls = 0
        self.errors = 0
        self.start_time = datetime.now()
    
    def log_status(self):
        uptime = datetime.now() - self.start_time
        hours, remainder = divmod(uptime.total_seconds(), 3600)
        minutes, seconds = divmod(remainder, 60)
        uptime_str = f"{int(hours)}h {int(minutes)}m {int(seconds)}s"
        
        logger.info(f"SERVER STATUS: Uptime: {uptime_str}, API Calls: {self.api_calls}, "
                   f"Resource Requests: {self.resource_requests}, Tool Calls: {self.tool_calls}, "
                   f"Errors: {self.errors}")

# Initialize stats
stats = ServerStats()

# Load environment variables
load_dotenv()

logger.info("Starting Senechal Health MCP Server")

# Create an MCP server
mcp = FastMCP("Senechal Health MCP")

# Constants
API_BASE_URL = os.getenv("SENECHAL_API_BASE_URL")
API_KEY = os.getenv("SENECHAL_API_KEY")

if not API_BASE_URL:
    logger.error("No API URL found. Please set SENECHAL_API_BASE_URL environment variable in .env file")
    raise ValueError("SENECHAL_API_BASE_URL environment variable is required")

if not API_KEY:
    logger.error("No API key found. Please set SENECHAL_API_KEY environment variable in .env file")
    raise ValueError("SENECHAL_API_KEY environment variable is required")

logger.info(f"Using API URL: {API_BASE_URL}")
logger.info(f"API Key: {'*' * len(API_KEY)}")

# Helper class for response types
@dataclass
class HealthSummary:
    period_type: str
    summaries: List[Dict[str, Any]]
    generated_at: str

@dataclass
class HealthProfile:
    markdown: str


@dataclass
class Metrics:
    markdown: str

# Helper functions
async def make_api_request(endpoint: str, params: Optional[Dict[str, Any]] = None, expect_json: bool = True) -> Any:
    """Make a request to the Senechal API with the API key."""
    headers = {"X-API-Key": API_KEY}
    
    # Log the request
    stats.api_calls += 1
    logger.info(f"API Request: {endpoint} - Params: {params}")
    stats.log_status()
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{API_BASE_URL}/{endpoint}", headers=headers, params=params)
            response.raise_for_status()
            logger.info(f"API Request successful: {endpoint}")
            if expect_json:
                return response.json()
            else:
                return response.text
    except Exception as e:
        stats.errors += 1
        logger.error(f"API Request failed: {endpoint} - Error: {str(e)}")
        raise

# Resources
@mcp.resource(uri="senechal://health/availablemetrics")
def get_available_metrics():
    """Get a list of available health metrics in markdown format."""
    async def impl(resource_uri, query_params):
        stats.resource_requests += 1
        logger.info(f"Resource Request: health/availablemetrics - Params: {query_params}")
        
        try:
            # Call the actual API, expecting markdown text instead of JSON
            data = await make_api_request("health/availablemetrics", expect_json=False)
            # Return as a Metrics object with markdown field
            return Metrics(markdown=data)
        except Exception as e:
            logger.error(f"API error in health/availablemetrics: {str(e)}")
            # Provide fallback data in case API fails
            return Metrics(markdown="# Error\n\nUnable to retrieve available health metrics. Please check your API key and connection.")
    
    return impl



@mcp.resource(uri="senechal://health/summary/{period}")
def get_health_summary(period: str):
    """
    Get a health summary for a specific period (day, week, month, year).
    
    Example: senechal://health/summary/day?metrics=all&span=7
    """
    async def impl(resource_uri, query_params):
        # Record stats
        stats.resource_requests += 1
        logger.info(f"Resource Request: health/summary/{period} - Params: {query_params}")
        
        # Convert query parameters for the API
        request_params = {}
        if 'metrics' in query_params:
            request_params['metrics'] = query_params['metrics']
        if 'span' in query_params:
            request_params['span'] = query_params['span']
        if 'offset' in query_params:
            request_params['offset'] = query_params['offset']
        
        # Call the actual API
        try:
            data = await make_api_request(f"health/summary/{period}", request_params)
            return data
        except Exception as e:
            logger.error(f"API error in health/summary/{period}: {str(e)}")
            # Provide fallback data in case API fails
            return {
                "error": f"API request failed: {str(e)}",
                "message": f"Unable to retrieve health summary data for period '{period}'. Please check your API key and connection."
            }
    
    return impl

@mcp.resource(uri="senechal://health/profile")
def get_health_profile():
    """Get the user's health profile in markdown format."""
    async def impl(resource_uri, query_params):
        stats.resource_requests += 1
        logger.info(f"Resource Request: health/profile - Params: {query_params}")
        
        try:
            # Call the actual API, expecting markdown text instead of JSON
            data = await make_api_request("health/profile", expect_json=False)
            # Return as a HealthProfile object with markdown field
            return HealthProfile(markdown=data)
        except Exception as e:
            logger.error(f"API error in health/profile: {str(e)}")
            # Provide fallback data in case API fails
            return HealthProfile(markdown="# Error\n\nUnable to retrieve health profile data. Please check your API key and connection.")
    
    return impl


# Tools
@mcp.tool()
async def fetch_available_metrics() -> str:
    """
    Fetch a list of available health metrics in markdown format.
    
    Returns:
        A markdown string containing the available metrics data
    """
    stats.tool_calls += 1
    logger.info("Tool Call: fetch_available_metrics")
    
    try:
        # Call the actual API, expecting markdown text
        data = await make_api_request("health/availablemetrics", expect_json=False)
        return data
    except Exception as e:
        logger.error(f"API error in fetch_available_metrics: {str(e)}")
        # Provide fallback data in case API fails
        return "# Error\n\nUnable to retrieve available health metrics. Please check your API key and connection."



@mcp.tool()
async def fetch_health_summary(period: str, metrics: str = "all", span: int = 1, offset: int = 0) -> Dict[str, Any]:
    """
    Fetch health summary for a specific period.
    
    Args:
        period: The period type (day, week, month, year)
        metrics: Comma-separated metrics/groups or 'all'
        span: Number of periods to return (1-52)
        offset: Number of periods to offset from now
    
    Returns:
        A dictionary containing the health summary data
    """
    stats.tool_calls += 1
    logger.info(f"Tool Call: fetch_health_summary - Args: period={period}, metrics={metrics}, span={span}, offset={offset}")
    
    # Parameters for the API request
    params = {
        'metrics': metrics,
        'span': span,
        'offset': offset
    }
    
    try:
        # Call the actual API
        data = await make_api_request(f"health/summary/{period}", params)
        return data
    except Exception as e:
        logger.error(f"API error in fetch_health_summary: {str(e)}")
        # Provide fallback data in case API fails
        return {
            "error": f"API request failed: {str(e)}",
            "message": f"Unable to retrieve health summary data for period '{period}'. Please check your API key and connection."
        }

@mcp.tool()
async def fetch_health_profile() -> str:
    """
    Fetch the user's health profile in markdown format.
    
    Returns:
        A markdown string containing the health profile data
    """
    stats.tool_calls += 1
    logger.info("Tool Call: fetch_health_profile")
    
    try:
        # Call the actual API, expecting markdown text
        data = await make_api_request("health/profile", expect_json=False)
        return data
    except Exception as e:
        logger.error(f"API error in fetch_health_profile: {str(e)}")
        # Provide fallback data in case API fails
        return "# Error\n\nUnable to retrieve health profile data. Please check your API key and connection."


# Prompts
@mcp.prompt()
def analyze_health_summary() -> str:
    """
    Create a prompt to analyze health summaries.
    """
    logger.info("Prompt Requested: analyze_health_summary")
    return """
    Please analyze the following health summary data and provide insights:
    
    1. Identify any metrics that are outside of normal ranges
    2. Highlight trends or patterns in the data
    3. Suggest potential actions based on the data
    
    You can load the health data from:
    - senechal://health/summary/day?span=7 for daily data
    - senechal://health/summary/week?span=4 for weekly data
    - senechal://health/summary/month?span=3 for monthly data
    
    For available metrics information, check senechal://health/availablemetrics
    """


# Run the server
if __name__ == "__main__":
    logger.info("Starting MCP server")
    mcp.run()