import requests
import os
from datetime import datetime
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv('API_KEY')
LEAGUE_ID = '4554'
YEAR = '2025'
BASE_URL = f'https://www.thesportsdb.com/api/v1/json/{API_KEY}'
SUPABASE_URL = os.getenv('NEXT_PUBLIC_SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY')

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def get_betmgm_premier_league_nights():
    try:
        response = requests.get(f'{BASE_URL}/eventsseason.php?id={LEAGUE_ID}&s={YEAR}')
        response.raise_for_status()
        events = response.json().get('events')

        if not events:
            print("No events found for the specified year.")
            return

        premier_league_events = [
            event for event in events 
            if "BetMGM Premier League Night" in event['strEvent'] and int(event['strEvent'].split()[-1]) <= 8
        ]

        if not premier_league_events:
            print("❌ No BetMGM Premier League Nights 1-8 found.")
            return

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

        response = supabase.table('darts').upsert(darts_data, on_conflict=['event_id']).execute()
        if hasattr(response, 'error') and response.error:
            print(f"❌ Error inserting into Supabase: {response.error.message}")
        else:
            print(f"✅ Inserted {len(darts_data)} events into Supabase at {datetime.now().strftime('%H:%M:%S GMT')}")

    except requests.RequestException as error:
        print("Error fetching darts events:", error)
    except Exception as e:
        print(f"Unexpected error: {e}")

if __name__ == "__main__":
    now = datetime.utcnow()
    start_utc = datetime(2025, 3, 6, 18, 0, 0)
    stop_utc = datetime(2025, 5, 30, 18, 0, 0)
    if start_utc <= now <= stop_utc:
        get_betmgm_premier_league_nights()
    else:
        print(f"Outside run window: {start_utc.strftime('%H:%M:%S GMT')} to {stop_utc.strftime('%H:%M:%S GMT')}")
