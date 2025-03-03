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
class CurrentHealth:
    measurements: List[Dict[str, Any]]
    timestamp: str
    timezone: str

@dataclass
class HealthTrends:
    trends: List[Dict[str, Any]]
    timestamp: str
    timezone: str

@dataclass
class HealthStats:
    stats: List[Dict[str, Any]]
    timestamp: str
    timezone: str

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
            # Return as a string since we're getting markdown
            return data
        except Exception as e:
            logger.error(f"API error in health/profile: {str(e)}")
            # Provide fallback data in case API fails
            return "# Error\n\nUnable to retrieve health profile data. Please check your API key and connection."
    
    return impl

@mcp.resource(uri="senechal://health/current")
def get_current_measurements():
    """
    Get the current health measurements.
    
    Example: senechal://health/current?types=1,2,3
    """
    async def impl(resource_uri, query_params):
        stats.resource_requests += 1
        logger.info(f"Resource Request: health/current - Params: {query_params}")
        
        # Convert query parameters for the API
        request_params = {}
        if 'types' in query_params:
            request_params['types'] = query_params['types']
        
        try:
            # Call the actual API
            data = await make_api_request("health/current", request_params)
            return data
        except Exception as e:
            logger.error(f"API error in health/current: {str(e)}")
            # Provide fallback data in case API fails
            return {
                "error": f"API request failed: {str(e)}",
                "message": "Unable to retrieve current health measurements. Please check your API key and connection."
            }
    
    return impl

@mcp.resource(uri="senechal://health/trends")
def get_health_trends():
    """
    Get health trends over time.
    
    Example: senechal://health/trends?days=30&types=1,2,3&interval=day
    """
    async def impl(resource_uri, query_params):
        stats.resource_requests += 1
        logger.info(f"Resource Request: health/trends - Params: {query_params}")
        
        # Convert query parameters for the API
        request_params = {}
        if 'days' in query_params:
            request_params['days'] = query_params['days']
        if 'types' in query_params:
            request_params['types'] = query_params['types']
        if 'interval' in query_params:
            request_params['interval'] = query_params['interval']
        
        try:
            # Call the actual API
            data = await make_api_request("health/trends", request_params)
            return data
        except Exception as e:
            logger.error(f"API error in health/trends: {str(e)}")
            # Provide fallback data in case API fails
            return {
                "error": f"API request failed: {str(e)}",
                "message": "Unable to retrieve health trend data. Please check your API key and connection."
            }
    
    return impl

@mcp.resource(uri="senechal://health/stats")
def get_health_stats():
    """
    Get statistical analysis of health metrics.
    
    Example: senechal://health/stats?days=30&types=1,2,3
    """
    async def impl(resource_uri, query_params):
        stats.resource_requests += 1
        logger.info(f"Resource Request: health/stats - Params: {query_params}")
        
        # Convert query parameters for the API
        request_params = {}
        if 'days' in query_params:
            request_params['days'] = query_params['days']
        if 'types' in query_params:
            request_params['types'] = query_params['types']
        
        try:
            # Call the actual API
            data = await make_api_request("health/stats", request_params)
            return data
        except Exception as e:
            logger.error(f"API error in health/stats: {str(e)}")
            # Provide fallback data in case API fails
            return {
                "error": f"API request failed: {str(e)}",
                "message": "Unable to retrieve health statistics data. Please check your API key and connection."
            }
    
    return impl

# Tools
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
    Fetch the user's health profile from the configured file location.
    
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

@mcp.tool()
async def fetch_current_health(types: Optional[List[int]] = None) -> Dict[str, Any]:
    """
    Fetch the latest measurements for all health metrics.
    
    Args:
        types: Optional filter by measurement types
    
    Returns:
        A dictionary containing the current health data
    """
    stats.tool_calls += 1
    logger.info(f"Tool Call: fetch_current_health - Args: types={types}")
    
    # Parameters for the API request
    params = {}
    if types:
        params['types'] = ','.join(map(str, types))
    
    try:
        # Call the actual API
        data = await make_api_request("health/current", params)
        return data
    except Exception as e:
        logger.error(f"API error in fetch_current_health: {str(e)}")
        # Provide fallback data in case API fails
        return {
            "error": f"API request failed: {str(e)}",
            "message": "Unable to retrieve current health measurements. Please check your API key and connection."
        }

@mcp.tool()
async def fetch_health_trends(days: int = 30, types: Optional[List[int]] = None, interval: str = "day") -> Dict[str, Any]:
    """
    Fetch trend data for specified period and metrics.
    
    Args:
        days: Number of days to analyze (default: 30)
        types: Optional filter by measurement types
        interval: Grouping interval: day, week, month (default: day)
    
    Returns:
        A dictionary containing the health trends data
    """
    stats.tool_calls += 1
    logger.info(f"Tool Call: fetch_health_trends - Args: days={days}, types={types}, interval={interval}")
    
    # Parameters for the API request
    params = {'days': days, 'interval': interval}
    if types:
        params['types'] = ','.join(map(str, types))
    
    try:
        # Call the actual API
        data = await make_api_request("health/trends", params)
        return data
    except Exception as e:
        logger.error(f"API error in fetch_health_trends: {str(e)}")
        # Provide fallback data in case API fails
        return {
            "error": f"API request failed: {str(e)}",
            "message": f"Unable to retrieve health trend data for the past {days} days. Please check your API key and connection."
        }

@mcp.tool()
async def fetch_health_stats(days: int = 30, types: Optional[List[int]] = None) -> Dict[str, Any]:
    """
    Fetch statistical analysis of health metrics.
    
    Args:
        days: Analysis period in days (default: 30)
        types: Optional filter by measurement types
    
    Returns:
        A dictionary containing the health stats data
    """
    stats.tool_calls += 1
    logger.info(f"Tool Call: fetch_health_stats - Args: days={days}, types={types}")
    
    # Parameters for the API request
    params = {'days': days}
    if types:
        params['types'] = ','.join(map(str, types))
    
    try:
        # Call the actual API
        data = await make_api_request("health/stats", params)
        return data
    except Exception as e:
        logger.error(f"API error in fetch_health_stats: {str(e)}")
        # Provide fallback data in case API fails
        return {
            "error": f"API request failed: {str(e)}",
            "message": f"Unable to retrieve health statistics data for the past {days} days. Please check your API key and connection."
        }

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
    
    The health data will be loaded from senechal://health/summary/day?span=7
    """

@mcp.prompt()
def compare_health_trends() -> str:
    """
    Create a prompt to compare health trends over different time periods.
    """
    logger.info("Prompt Requested: compare_health_trends")
    return """
    Please compare the following health trend data:
    
    1. Compare trends over the specified time periods
    2. Identify significant changes or patterns
    3. Suggest potential explanations for observed changes
    
    The health data will be loaded from:
    - senechal://health/trends?days=7&interval=day
    - senechal://health/trends?days=30&interval=day
    - senechal://health/trends?days=90&interval=week
    """

# Run the server
if __name__ == "__main__":
    logger.info("Starting MCP server")
    mcp.run()