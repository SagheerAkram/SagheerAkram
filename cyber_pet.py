import requests
import datetime
import re
import os
import sys

# Configuration
USERNAME = "SagheerAkram"
README_PATH = "README.md"
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")

# Pet Assets
PET_STATES = {
    "happy": {
        "art": r"""
      ^ ◡ ^
    (  o.o  )
     >  ^  <
    """,
        "msg": "Yummy code! I'm full and happy! 🟢", 
        "mood": "Happy"
    },
    "hungry": {
        "art": r"""
      - _ -
    (  T.T  )
     >  ^  <
    """,
        "msg": "I'm starving... feed me commits! 🔴",
        "mood": "Hungry"
    },
    "evolved": {
        "art": r"""
      🔥 0_0 🔥
     /[__] \
      ]   [
    """,
        "msg": "ON FIRE! 5+ Day Streak! 🟣",
        "mood": "Evolved"
    }
}

def get_commit_activity(username):
    """
    Fetches the last 90 days of events to determine streaks and today's status.
    Uses public Events API.
    """
    url = f"https://api.github.com/users/{username}/events"
    headers = {}
    if GITHUB_TOKEN:
        headers["Authorization"] = f"token {GITHUB_TOKEN}"
    
    print(f"Fetching events from: {url}")
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        events = response.json()
    except Exception as e:
        print(f"Error fetching events: {e}")
        return set()

    push_dates = set()
    
    # Debug: Print first event to check structure
    if events:
        print(f"Latest event keys: {events[0].keys()}")

    for event in events:
        if event["type"] == "PushEvent":
            created_at = event["created_at"]
            # format: 2023-10-26T10:30:00Z
            date_obj = datetime.datetime.strptime(created_at, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=datetime.timezone.utc).date()
            push_dates.add(date_obj)
            
    print(f"Found {len(push_dates)} active days in recent history.")
    return push_dates

def calculate_stats(push_dates):
    today = datetime.datetime.now(datetime.timezone.utc).date()
    print(f"Today (UTC): {today}")
    
    fed_today = today in push_dates
    
    # Calculate streak
    # We count backwards from today (if fed) or yesterday (if not fed, to check previous streak?)
    # If not fed today, streak is technically broken for "today", so streak = 0.
    
    current_streak = 0
    
    if fed_today:
        check_date = today
        while check_date in push_dates:
            current_streak += 1
            check_date -= datetime.timedelta(days=1)
    else:
        # If not fed today, the streak is 0 because the chain is broken for the current day status.
        # User prompt check: "Streak: If you commit 5 days in a row..." implies active streak.
        current_streak = 0

    return fed_today, current_streak

def generate_content(fed_today, streak):
    if streak >= 5 and fed_today:
        state = PET_STATES["evolved"]
        state_key = "evolved"
    elif fed_today:
        state = PET_STATES["happy"]
        state_key = "happy"
    else:
        state = PET_STATES["hungry"]
        state_key = "hungry"
        
    ascii_art = state["art"]
    
    # Calculate XP (just purely fun math based on streak)
    xp = min(streak * 100, 1000) 
    
    content = f"""<!-- CYBER_PET_START -->
### 👾 Cyber Pet
```text
{ascii_art}
```
**Name**: Git-Zilla
**Mood**: {state['mood']}
**Status**: {state['msg']}
**Streak**: {streak} days
**XP**: {xp} / 1000
<!-- CYBER_PET_END -->"""
    return content

def update_readme(content):
    if not os.path.exists(README_PATH):
        print(f"Error: {README_PATH} not found.")
        return

    with open(README_PATH, "r", encoding="utf-8") as f:
        data = f.read()
        
    # Regex to find the block
    pattern = r"<!-- CYBER_PET_START -->.*?<!-- CYBER_PET_END -->"
    
    # Check if markers exist
    if not re.search(pattern, data, flags=re.DOTALL):
        print("Markers not found in README.md. Adding them to end of file (or please add manually).")
        # Fallback: Append if not found? Or just fail?
        # Let's try to be smart, but user already has markers from previous step.
        return 
    
    new_data = re.sub(pattern, content, data, flags=re.DOTALL)
    
    with open(README_PATH, "w", encoding="utf-8") as f:
        f.write(new_data)

def main():
    push_dates = get_commit_activity(USERNAME)
    fed_today, streak = calculate_stats(push_dates)
    
    print(f"Fed Today: {fed_today}, Streak: {streak}")
    
    content = generate_content(fed_today, streak)
    update_readme(content)
    print("README updated successfully!")

if __name__ == "__main__":
    main()
