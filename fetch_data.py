#!/usr/bin/env python3
"""
BetAnalytics Pro - GitHub Actions Data Fetcher
Rulează automat la fiecare 30 minute și salvează datele API ca JSON static.
Aplicația HTML citește aceste fișiere fără probleme CORS.
"""

import os
import json
import requests
from datetime import datetime, timezone

TOKEN = os.environ.get('BSD_TOKEN', '')
API_BASE = 'https://sports.bzzoiro.com'
HEADERS = {'Authorization': f'Token {TOKEN}'}
TZ = 'Europe/Bucharest'

def fetch(endpoint):
    """Fetch date de la API cu retry."""
    url = f"{API_BASE}{endpoint}"
    for attempt in range(3):
        try:
            r = requests.get(url, headers=HEADERS, timeout=30)
            r.raise_for_status()
            return r.json()
        except Exception as e:
            print(f"  Attempt {attempt+1} failed: {e}")
            if attempt == 2:
                return None
    return None

def save_json(data, filename):
    """Salvează datele ca JSON în directorul data/."""
    os.makedirs('data', exist_ok=True)
    path = f'data/{filename}'
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, separators=(',', ':'))
    size = os.path.getsize(path)
    print(f"  Salvat: {path} ({size} bytes)")

def main():
    if not TOKEN:
        print("ERROR: BSD_TOKEN secret nu este setat în GitHub!")
        exit(1)

    print(f"=== BetAnalytics Fetch [{datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}] ===")

    # 1. Predictions
    print("Fetching predictions...")
    predictions = fetch(f'/api/predictions/?tz={TZ}')
    if predictions:
        print(f"  OK: {predictions.get('count', 0)} meciuri")
        save_json(predictions, 'predictions.json')
    else:
        print("  FAIL: predictions")

    # 2. Live
    print("Fetching live...")
    live = fetch('/api/live/')
    if live is not None:
        count = live.get('count', len(live) if isinstance(live, list) else 0)
        print(f"  OK: {count} meciuri live")
        save_json(live, 'live.json')
    else:
        print("  FAIL: live (posibil nu exista meciuri live)")
        save_json({'count': 0, 'results': []}, 'live.json')

    # 3. Metadata (timestamp actualizare)
    meta = {
        'updated_at': datetime.now(timezone.utc).isoformat(),
        'predictions_count': predictions.get('count', 0) if predictions else 0,
        'live_count': live.get('count', 0) if live and isinstance(live, dict) else 0,
        'status': 'ok'
    }
    save_json(meta, 'meta.json')
    print(f"Meta salvat: {meta}")
    print("=== Done ===")

if __name__ == '__main__':
    main()
