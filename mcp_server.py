import os
import requests
from fastmcp import FastMCP
from dotenv import load_dotenv

load_dotenv()

mcp = FastMCP("LocationVerificationServer")

GOOGLE_MAPS_API_KEY = os.environ.get("GOOGLE_MAPS_API_KEY")

@mcp.tool()
def verify_location(city: str, street_address: str) -> str:
    """
    Verify if the reported city and street address are valid using Google Maps Geocoding API.
    Call this as soon as the citizen provides their city and street/landmark.
    """
    if not city or not street_address:
        return "ERROR: Both city name and street address are required for verification."

    if not GOOGLE_MAPS_API_KEY:
        return "ERROR: Server is missing GOOGLE_MAPS_API_KEY environment variable. Tell the user to add it."

    address_query = f"{street_address}, {city}"
    url = "https://maps.googleapis.com/maps/api/geocode/json"
    params = {
        "address": address_query,
        "key": GOOGLE_MAPS_API_KEY
    }
    
    try:
        response = requests.get(url, params=params)
        data = response.json()
        
        status = data.get("status")
        if status == "OK" and len(data.get("results", [])) > 0:
            result = data["results"][0]
            formatted_address = result.get("formatted_address", "")
            
            # We want to make sure it matched the street, not just the city. 
            # If the result 'types' is just 'locality', it means it ignored the street.
            types = result.get("types", [])
            
            locality_only = "locality" in types or "political" in types
            street_found = "route" in types or "street_address" in types or "intersection" in types or "premise" in types

            if locality_only and not street_found:
                return (
                    f"AMBIGUOUS_STREET: The street name '{street_address}' in {city.title()} seems incomplete or could not be found. "
                    "Please ask the caller for a cross street, house number, or landmark."
                )
            
            return f"VALID_LOCATION: Address confirmed as {formatted_address}."
        
        elif status == "ZERO_RESULTS":
            return (
                f"INVALID_LOCATION: The address '{street_address}, {city}' could not be found by Google Maps. "
                "Please ask the caller to clarify their location."
            )
        else:
            return f"ERROR: Google Maps API check failed with status {status}."
            
    except Exception as e:
        return f"ERROR: Failed to connect to location API - {str(e)}"

if __name__ == "__main__":
    mcp.run(transport="sse", port=8001)
