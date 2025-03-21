import requests
import os
from datetime import datetime
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables from .env file (if present)
load_dotenv()

# Environment variables
API_KEY = os.getenv('API_KEY')
LEAGUE_ID = '4554'
YEAR = '2025'
BASE_URL = f'https://www.thesportsdb.com/api/v1/json/{API_KEY}'
SUPABASE_URL = os.getenv('NEXT_PUBLIC_SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY')

# Initialize Supabase client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def get_betmgm_premier_league_nights():
    try:
        # Fetch events from TheSportsDB API
        response = requests.get(f'{BASE_URL}/eventsseason.php?id={LEAGUE_ID}&s={YEAR}')
        response.raise_for_status()
        events = response.json().get('events')

        if not events:
            print("No events found for the specified year.")
            return

        # Filter for BetMGM Premier League Nights 1-8
        premier_league_events = [
            event for event in events 
            if "BetMGM Premier League Night" in event['strEvent'] and int(event['strEvent'].split()[-1]) <= 8
        ]

        if not premier_league_events:
            print("❌ No BetMGM Premier League Nights 1-8 found.")
            return

        # Prepare data for Supabase
        darts_data = []
        for event in premier_league_events:
            darts_event = {
                'event_id': event.get('idEvent'),
                'event_name': event.get('strEvent'),
                'date_event': event.get('dateEvent'),
                'time_event': event.get('strTime', 'No time available'),
                'description': event.get('strDescriptionEN', 'No description available'),
                'venue': event.get('strVenue', 'No venue information'),
                'city': event.get('strCity', 'No city information'),
                'country': event.get('strCountry', 'No country information'),
                'season': event.get('strSeason', 'No season information'),
                'result': event.get('strResult', 'No result information'),
                'status': event.get('strStatus', 'No status information'),
                'postponed': event.get('strPostponed', 'No postponement information'),
                'spectators': int(event.get('intSpectators', 0)) if event.get('intSpectators') else 0,
                'official': event.get('strOfficial', 'No official information'),
                'created_at': datetime.utcnow().isoformat()
            }
            darts_data.append(darts_event)

        # Upsert data into Supabase
        response = supabase.table('darts').upsert(darts_data, on_conflict=['event_id']).execute()
        if hasattr(response, 'error') and response.error:
            print(f"❌ Error inserting into Supabase: {response.error.message}")
        else:
            print(f"✅ Inserted {len(darts_data)} events into Supabase at {datetime.utcnow().strftime('%H:%M:%S GMT')}")

    except requests.RequestException as error:
        print("Error fetching darts events:", error)
    except Exception as e:
        print(f"Unexpected error: {e}")

if __name__ == "__main__":
    # Current UTC time
    now = datetime.utcnow()

    # Define the recurring window
    start_utc = datetime(2025, 3, 6, 18, 0, 0)  # March 6, 2025, 18:00 UTC
    stop_utc = datetime(2025, 5, 30, 18, 0, 0)  # May 30, 2025, 18:00 UTC

    # Define one-off run times
    one_off_saturday = datetime(2025, 5, 30, 18, 0, 0)  # May 30, 2025, 18:00 UTC
    one_off_sunday = datetime(2025, 5, 31, 12, 0, 0)    # May 31, 2025, 12:00 UTC

    # Check if current time falls within recurring window or matches one-off times
    # Remove microseconds from 'now' for exact comparison with one-off dates
    if (start_utc <= now <= stop_utc) or now.replace(microsecond=0) == one_off_saturday or now.replace(microsecond=0) == one_off_sunday:
        get_betmgm_premier_league_nights()
    else:
        print(f"Outside run window: {start_utc.strftime('%H:%M:%S GMT')} to {stop_utc.strftime('%H:%M:%S GMT')} and one-off dates")
