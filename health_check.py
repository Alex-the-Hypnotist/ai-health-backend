import feedparser
import json
import os
from datetime import datetime, timedelta, timezone

# --- CONFIGURATION ---
# We check these RSS feeds for "Smoke Signals"
MODELS = {
    "GPT-4": {
        "rss": "https://www.reddit.com/r/ChatGPT/new.rss",
        "slow_words": ["slow", "lag", "stuck", "taking forever", "latency", "spinning"],
        "down_words": ["down", "outage", "broken", "error", "service unavailable", "crash"]
    },
    "Gemini": {
        "rss": "https://www.reddit.com/r/GeminiAI/new.rss",
        "slow_words": ["slow", "lag", "thinking", "stuck"],
        "down_words": ["down", "outage", "broken", "error"]
    },
    "Claude": {
        "rss": "https://www.reddit.com/r/ClaudeAI/new.rss",
        "slow_words": ["slow", "lag", "limit", "stuck", "wait"],
        "down_words": ["down", "outage", "refusal", "error", "404", "ban"]
    },
    "Grok": {
        "rss": "https://www.reddit.com/r/Grok/new.rss", # Using r/Grok (smaller sub, less noise)
        "slow_words": ["slow", "lag", "wait"],
        "down_words": ["down", "outage", "broken", "error"]
    }
}

# The Logic: "Rule of 4 in 2"
# If >3 people complain in 2 hours, it's a warning.
TIME_LIMIT = timedelta(hours=2) 

def check_health():
    final_status = {}
    
    for name, config in MODELS.items():
        print(f"Checking {name}...")
        try:
            feed = feedparser.parse(config['rss'])
            slow_count = 0
            down_count = 0
            
            # Check last 25 posts
            for entry in feed.entries[:25]:
                # Check Time
                try:
                    post_time = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
                    if (datetime.now(timezone.utc) - post_time) > TIME_LIMIT:
                        continue # Skip old posts
                except:
                    continue # Skip if time parsing fails

                title = entry.title.lower()
                
                # Check Keywords
                if any(w in title for w in config['down_words']):
                    down_count += 1
                elif any(w in title for w in config['slow_words']):
                    slow_count += 1
            
            # Decide Status
            if down_count >= 4:
                status = "CRITICAL"
                sentiment = "Outage Reports"
                latency = "Down"
                color = "red"
            elif slow_count >= 3:
                status = "WARNING"
                sentiment = "Lag Reports"
                latency = "Slow"
                color = "yellow"
            else:
                status = "NORMAL"
                sentiment = "Quiet"
                latency = "Normal"
                color = "green"
                
            final_status[name] = {
                "status": status,
                "sentiment": sentiment,
                "latency": latency,
                "color": color
            }
            
        except Exception as e:
            print(f"Error checking {name}: {e}")
            # Fallback if Reddit fails
            final_status[name] = {
                "status": "UNKNOWN", 
                "sentiment": "No Data", 
                "latency": "?", 
                "color": "yellow"
            }

    # Save to JSON file
    with open('status.json', 'w') as f:
        json.dump(final_status, f, indent=2)

if __name__ == "__main__":
    check_health()
