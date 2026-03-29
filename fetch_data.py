#!/usr/bin/env python3
"""
BetAnalytics Pro V2 - GitHub Actions Data Fetcher
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

# Fallback: citește datele din V1 (BetAnalyticsPro) dacă tokenul nu e setat
V1_BASE = 'https://balty1991.github.io/BetAnalyticsPro/data'

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

def fetch_from_v1(filename):
    """Fallback: citeste datele din V1 GitHub Pages."""
    url = f"{V1_BASE}/{filename}?t={int(datetime.now().timestamp())}"
    try:
        r = requests.get(url, timeout=30)
        r.raise_for_status()
        data = r.json()
        print(f"  Fallback V1 OK: {url}")
        return data
    except Exception as e:
        print(f"  Fallback V1 FAIL: {e}")
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
    print(f"=== BetAnalytics V2 Fetch [{datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}] ===")

    predictions = None
    live = None

    if TOKEN:
        print("Fetching predictions from API...")
        predictions = fetch(f'/api/predictions/?tz={TZ}')
        if predictions:
            print(f"  OK: {predictions.get('count', 0)} meciuri")
        else:
            print("  FAIL: predictions din API")

        print("Fetching live from API...")
        live = fetch('/api/live/')
        if live is not None:
            count = live.get('count', len(live) if isinstance(live, list) else 0)
            print(f"  OK: {count} meciuri live")
        else:
            print("  FAIL: live din API")
    else:
        print("WARN: BSD_TOKEN nu este setat - folosim fallback V1")

    # Fallback la V1 dacă API-ul nu funcționează
    if not predictions:
        print("Fallback: citire predictions din V1...")
        predictions = fetch_from_v1('predictions.json')

    if live is None:
        print("Fallback: citire live din V1...")
        live = fetch_from_v1('live.json')
        if live is None:
            live = {'count': 0, 'results': []}

    # Salvare date
    if predictions:
        save_json(predictions, 'predictions.json')
    else:
        print("ERROR: Nu s-au putut obține predicțiile!")
        exit(1)

    save_json(live if live else {'count': 0, 'results': []}, 'live.json')

    # Metadata
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
