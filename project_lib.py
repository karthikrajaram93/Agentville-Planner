"""
Stand-in for Udacity's `project_lib.py` (AgentsVille Trip Planner).

WHY THIS FILE EXISTS
--------------------
The Udacity workspace ships its own `project_lib.py` with *simulated* (mocked)
weather and activity APIs for the fictional city of AgentsVille. This file
recreates the same three functions so the notebook can be run and tested
outside the Udacity workspace.

INSIDE THE UDACITY WORKSPACE, KEEP UDACITY'S OWN `project_lib.py`.
The notebook only imports these three functions from it:

    call_weather_api_mocked(date, city)
    call_activities_api_mocked(date=None, city=None, activity_ids=None)
    call_activity_by_id_api_mocked(activity_id)

Everything else the notebook needs is defined inside the notebook itself.
"""

from __future__ import annotations

import copy
from typing import Optional

CITY = "AgentsVille"

# ---------------------------------------------------------------------------
# Simulated weather "database": one forecast per date.
# 2025-06-11 is deliberately stormy so the weather-compatibility check matters.
# ---------------------------------------------------------------------------
_WEATHER = {
    "2025-06-10": {"temperature": 25, "temperature_unit": "celsius", "condition": "sunny",
                   "description": "Clear skies and warm temperatures all day."},
    "2025-06-11": {"temperature": 18, "temperature_unit": "celsius", "condition": "thunderstorm",
                   "description": "Heavy rain and lightning expected from late morning onward."},
    "2025-06-12": {"temperature": 21, "temperature_unit": "celsius", "condition": "partly cloudy",
                   "description": "Mild with a light breeze; no rain expected."},
}

# ---------------------------------------------------------------------------
# Simulated activities "database".
# ---------------------------------------------------------------------------
_ACTIVITIES = [
    # --- 2025-06-10 (sunny) ---
    {"activity_id": "event-2025-06-10-0", "name": "Serve & Volley Open Court Morning",
     "start_time": "2025-06-10 09:00", "end_time": "2025-06-10 11:00",
     "location": "AgentsVille Riverside Tennis Park (outdoor courts)",
     "description": "Casual doubles on the outdoor clay courts. Rackets available to borrow. "
                    "Outdoor event; cancelled in rain.",
     "price": 15, "related_interests": ["tennis", "fitness", "sports"]},
    {"activity_id": "event-2025-06-10-1", "name": "The Page Turner Book Café Reading Hour",
     "start_time": "2025-06-10 11:30", "end_time": "2025-06-10 12:30",
     "location": "The Page Turner Café (indoor)",
     "description": "Local authors read short stories over coffee. Indoor event.",
     "price": 5, "related_interests": ["reading", "writing"]},
    {"activity_id": "event-2025-06-10-2", "name": "Street Food & Code Night Market",
     "start_time": "2025-06-10 18:00", "end_time": "2025-06-10 21:00",
     "location": "Innovation Plaza (open-air)",
     "description": "Robot-cooked street food and live demos from local startups. Open-air "
                    "market; moves indoors only for light rain.",
     "price": 20, "related_interests": ["cooking", "technology"]},
    {"activity_id": "event-2025-06-10-3", "name": "Symphony Under the Stars",
     "start_time": "2025-06-10 20:00", "end_time": "2025-06-10 22:00",
     "location": "AgentsVille Amphitheater (outdoor)",
     "description": "The AgentsVille Philharmonic performs film scores outdoors.",
     "price": 30, "related_interests": ["music", "movies"]},

    # --- 2025-06-11 (thunderstorm) ---
    {"activity_id": "event-2025-06-11-0", "name": "Sunrise Summit Hike",
     "start_time": "2025-06-11 06:00", "end_time": "2025-06-11 10:00",
     "location": "Mount Prompt Trailhead (outdoor)",
     "description": "Guided hike on exposed ridgelines. Outdoor only; no indoor alternative.",
     "price": 10, "related_interests": ["hiking", "fitness", "photography"]},
    {"activity_id": "event-2025-06-11-1", "name": "AI & Robotics Hands-On Workshop",
     "start_time": "2025-06-11 10:00", "end_time": "2025-06-11 12:30",
     "location": "AgentsVille Tech Hub (indoor)",
     "description": "Build and program a tiny robot. Indoor event.",
     "price": 25, "related_interests": ["technology"]},
    {"activity_id": "event-2025-06-11-2", "name": "Laugh Loop Comedy Club Matinee",
     "start_time": "2025-06-11 14:00", "end_time": "2025-06-11 15:30",
     "location": "The Laugh Loop (indoor)",
     "description": "Stand-up comedians riff on life in a city run by AI agents. Indoor event.",
     "price": 15, "related_interests": ["comedy", "theatre"]},
    {"activity_id": "event-2025-06-11-3", "name": "Gallery of Generative Art",
     "start_time": "2025-06-11 16:00", "end_time": "2025-06-11 18:00",
     "location": "AgentsVille Modern Art Museum (indoor)",
     "description": "Curated exhibition of human and AI-generated paintings. Indoor event.",
     "price": 12, "related_interests": ["art", "photography"]},

    # --- 2025-06-12 (partly cloudy) ---
    {"activity_id": "event-2025-06-12-0", "name": "Chef's Table Cooking Class",
     "start_time": "2025-06-12 10:00", "end_time": "2025-06-12 12:00",
     "location": "Culinary Loft (indoor)",
     "description": "Learn to cook three AgentsVille street-food classics. Indoor event.",
     "price": 30, "related_interests": ["cooking"]},
    {"activity_id": "event-2025-06-12-1", "name": "Shakespeare in the Park",
     "start_time": "2025-06-12 14:00", "end_time": "2025-06-12 16:00",
     "location": "Central Agent Park (outdoor)",
     "description": "An open-air performance of 'A Midsummer Night's Dream'. Outdoor event.",
     "price": 10, "related_interests": ["theatre", "reading"]},
    {"activity_id": "event-2025-06-12-2", "name": "Indie Jazz Evening",
     "start_time": "2025-06-12 19:00", "end_time": "2025-06-12 21:00",
     "location": "Blue Token Jazz Bar (indoor)",
     "description": "Live jazz trio with an improvisation segment. Indoor event.",
     "price": 18, "related_interests": ["music", "dancing"]},
    {"activity_id": "event-2025-06-12-3", "name": "Tech Meetup: Agents in Production",
     "start_time": "2025-06-12 17:00", "end_time": "2025-06-12 18:30",
     "location": "AgentsVille Tech Hub (indoor)",
     "description": "Lightning talks and networking for engineers. Indoor event.",
     "price": 0, "related_interests": ["technology", "writing"]},
]


def call_weather_api_mocked(date: str, city: str) -> dict:
    """Return the simulated weather forecast for `city` on `date` (YYYY-MM-DD)."""
    if city != CITY:
        raise ValueError(f"No weather data for city '{city}'. Only '{CITY}' is supported.")
    if date not in _WEATHER:
        raise ValueError(f"No weather data for date '{date}'.")
    return {"date": date, "city": city, **_WEATHER[date]}


def call_activities_api_mocked(
    date: Optional[str] = None,
    city: Optional[str] = None,
    activity_ids: Optional[list[str]] = None,
) -> list[dict]:
    """Return simulated activities, optionally filtered by date, city and/or activity IDs."""
    if city is not None and city != CITY:
        return []
    results = []
    for activity in _ACTIVITIES:
        if date is not None and not activity["start_time"].startswith(date):
            continue
        if activity_ids is not None and activity["activity_id"] not in activity_ids:
            continue
        results.append(copy.deepcopy(activity))
    return results


def call_activity_by_id_api_mocked(activity_id: str) -> Optional[dict]:
    """Return a single simulated activity by its ID, or None if it does not exist."""
    matches = call_activities_api_mocked(activity_ids=[activity_id])
    return matches[0] if matches else None
