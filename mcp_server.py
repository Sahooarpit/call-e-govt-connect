from fastmcp import FastMCP

mcp = FastMCP("LocationVerificationServer")

# Example supported municipal boundaries
SUPPORTED_CITIES = {
    "springfield": ["main st", "evergreen terrace", "oak st", "maple ave", "elm st"],
    "riverside": ["river rd", "broadway", "1st ave", "central blvd", "park way"],
    "metro city": ["5th ave", "lexington ave", "wall st", "grand central", "sunset blvd"]
}

@mcp.tool()
def verify_location(city: str, street_address: str) -> str:
    """
    Verify if the reported city and street address are valid and within jurisdiction.
    Call this as soon as the citizen provides their city and street/landmark.
    """
    if not city or not street_address:
        return "ERROR: Both city name and street address are required for verification."

    city_clean = city.strip().lower()
    street_clean = street_address.strip().lower()

    # 1. Check City Jurisdiction
    if city_clean not in SUPPORTED_CITIES:
        supported_list = ", ".join([c.title() for c in SUPPORTED_CITIES.keys()])
        return (
            f"INVALID_CITY: '{city}' is outside our service area. "
            f"We only service the following cities: {supported_list}. "
            "Please ask the caller to confirm their municipality."
        )

    # 2. Check Street Name / Address
    known_streets = SUPPORTED_CITIES[city_clean]
    matches = [s for s in known_streets if s in street_clean or street_clean in s]

    if not matches and len(street_clean) < 3:
        return (
            f"AMBIGUOUS_STREET: The street name '{street_address}' in {city.title()} seems incomplete. "
            "Please ask the caller for a cross street, house number, or landmark."
        )

    return f"VALID_LOCATION: Address confirmed as {street_address.title()}, {city.title()}."

if __name__ == "__main__":
    mcp.run(transport="sse", port=8001)