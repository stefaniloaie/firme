"""
Google Places API - firme fara site web dintr-un judet Romania

Strategia optimizata:
  1. Nearby Search pe fiecare tip de business
  2. Place Details DOAR pentru firmele fara website
  3. Filtrare dupa judet prin keywords in adresa

Necesar: GOOGLE_PLACES_API_KEY in .env

Usage:
    python main.py                                      # Bistrita-Nasaud (default)
    python main.py --region cluj                        # Cluj
    python main.py --region custom --lat 46.77 --lng 23.62 --county-keywords "cluj" "cluj-napoca" --county-name Cluj
    python main.py --types restaurant store
    python main.py --output output/results
"""

import argparse
import csv
import json
import os
import sys
import time
from pathlib import Path

import httpx
from dotenv import load_dotenv
from rich.console import Console
from rich.progress import track
from rich.table import Table

load_dotenv()
console = Console()

PLACES_API_BASE = "https://maps.googleapis.com/maps/api/place"

SEARCH_TYPES = [
    "restaurant", "food", "store", "lodging", "beauty_salon",
    "car_repair", "clothing_store", "dentist", "doctor", "electrician",
    "gym", "hardware_store", "home_goods_store", "hospital", "laundry",
    "locksmith", "moving_company", "painter", "pet_store", "pharmacy",
    "physiotherapist", "plumber", "real_estate_agency", "roofing_contractor",
    "shoe_store", "spa", "supermarket", "travel_agency", "veterinary_care",
    "accounting", "lawyer",
]

DETAILS_FIELDS = "name,website,formatted_phone_number,formatted_address,business_status"

REGIONS = {
    "bistrita": {
        "name": "Bistrița-Năsăud",
        "lat": 47.1322, "lng": 24.4980, "radius": 60_000,
        "keywords": ["bistrița", "bistrita", "bistrita-nasaud", "bistrița-năsăud",
                     "năsăud", "nasaud", "beclean", "sângeorz", "singeorz",
                     "jud. bn", "jud.bn"],
    },
    "cluj": {
        "name": "Cluj",
        "lat": 46.7712, "lng": 23.6236, "radius": 60_000,
        "keywords": ["cluj", "cluj-napoca", "turda", "câmpia turzii", "campia turzii",
                     "dej", "gherla", "huedin", "jud. cj", "jud.cj", ", cj,", " cj "],
    },
    "brasov": {
        "name": "Brașov",
        "lat": 45.6427, "lng": 25.5887, "radius": 60_000,
        "keywords": ["brașov", "brasov", "săcele", "sacele", "râșnov", "rasnov",
                     "predeal", "zărnești", "zarnesti", "jud. bv", "jud.bv"],
    },
    "sibiu": {
        "name": "Sibiu",
        "lat": 45.7983, "lng": 24.1256, "radius": 60_000,
        "keywords": ["sibiu", "mediaș", "medias", "cisnădie", "cisnadie",
                     "agnita", "jud. sb", "jud.sb"],
    },
    "timisoara": {
        "name": "Timiș",
        "lat": 45.7489, "lng": 21.2087, "radius": 60_000,
        "keywords": ["timișoara", "timisoara", "lugoj", "jimbolia", "sânnicolau",
                     "sannicolau", "jud. tm", "jud.tm"],
    },
}


def nearby_search(api_key: str, place_type: str, lat: float, lng: float,
                  radius: int, page_token: str | None = None) -> dict:
    if page_token:
        params = {"key": api_key, "pagetoken": page_token}
    else:
        params = {
            "key": api_key,
            "location": f"{lat},{lng}",
            "radius": radius,
            "type": place_type,
            "language": "ro",
        }
    resp = httpx.get(f"{PLACES_API_BASE}/nearbysearch/json", params=params, timeout=15)
    resp.raise_for_status()
    return resp.json()


def get_place_details(api_key: str, place_id: str) -> dict:
    params = {
        "key": api_key,
        "place_id": place_id,
        "fields": DETAILS_FIELDS,
        "language": "ro",
    }
    resp = httpx.get(f"{PLACES_API_BASE}/details/json", params=params, timeout=15)
    resp.raise_for_status()
    return resp.json().get("result", {})


def is_in_county(address: str, keywords: list[str]) -> bool:
    al = address.lower()
    return any(k in al for k in keywords)


def main():
    parser = argparse.ArgumentParser(description="Firme fara site dintr-un judet Romania")
    parser.add_argument("--region", default="bistrita",
                        choices=list(REGIONS.keys()) + ["custom"],
                        help="Judetul de cautat (default: bistrita)")
    parser.add_argument("--lat",   type=float, help="Latitudine (doar pentru --region custom)")
    parser.add_argument("--lng",   type=float, help="Longitudine (doar pentru --region custom)")
    parser.add_argument("--radius",type=int, default=60_000, help="Raza cautare in metri (default: 60000)")
    parser.add_argument("--county-keywords", nargs="+", help="Cuvinte cheie judet (pentru --region custom)")
    parser.add_argument("--county-name", default="Custom", help="Numele judetului afisat")
    parser.add_argument("--output", default="", help="Prefix fisier output (default: output/firme_fara_site_<region>)")
    parser.add_argument("--types", nargs="+", help="Tipuri de locatii (default: toate)")
    parser.add_argument("--no-filter-county", action="store_true")
    args = parser.parse_args()

    api_key = os.getenv("GOOGLE_PLACES_API_KEY")
    if not api_key:
        console.print("[red]Eroare: GOOGLE_PLACES_API_KEY nu e setat in .env[/red]")
        sys.exit(1)

    # Configurare regiune
    if args.region == "custom":
        if not args.lat or not args.lng or not args.county_keywords:
            console.print("[red]--region custom necesita --lat, --lng si --county-keywords[/red]")
            sys.exit(1)
        region = {
            "name": args.county_name,
            "lat": args.lat, "lng": args.lng,
            "radius": args.radius,
            "keywords": [k.lower() for k in args.county_keywords],
        }
    else:
        region = REGIONS[args.region]
        if args.radius != 60_000:
            region = {**region, "radius": args.radius}

    output_prefix = args.output or f"output/firme_fara_site_{args.region}"
    output_path = Path(output_prefix)
    output_path.parent.mkdir(exist_ok=True)

    types_to_search = args.types or SEARCH_TYPES

    console.print(f"\n[bold]Regiune:[/bold] {region['name']} | raza {region['radius']//1000}km")

    # ── PASUL 1: Nearby Search ───────────────────────────────────────────────
    console.print("\n[bold cyan]Pasul 1:[/bold cyan] Nearby Search pe toate tipurile...")
    all_place_ids: set[str] = set()
    raw_places: list[dict] = []
    nearby_req_count = 0

    for ptype in track(types_to_search, description="Nearby Search..."):
        page_token = None
        while True:
            data = nearby_search(api_key, ptype, region["lat"], region["lng"],
                                 region["radius"], page_token)
            nearby_req_count += 1
            status = data.get("status")
            if status not in ("OK", "ZERO_RESULTS"):
                break
            for p in data.get("results", []):
                pid = p.get("place_id")
                if pid and pid not in all_place_ids:
                    all_place_ids.add(pid)
                    raw_places.append(p)
            page_token = data.get("next_page_token")
            if not page_token:
                break
            time.sleep(2)
        time.sleep(0.1)

    console.print(f"  → {len(raw_places)} locatii unice | {nearby_req_count} requests Nearby Search")

    # ── PASUL 2: Filtreaza dupa judet ────────────────────────────────────────
    if not args.no_filter_county:
        filtered = [p for p in raw_places
                    if is_in_county(p.get("vicinity", "") + " " + p.get("name", ""),
                                    region["keywords"])]
        console.print(f"  → {len(filtered)} locatii dupa filtru judet (din {len(raw_places)})")
    else:
        filtered = raw_places

    # ── PASUL 3: Place Details ────────────────────────────────────────────────
    console.print(f"\n[bold cyan]Pasul 2:[/bold cyan] Place Details pentru {len(filtered)} locatii...")
    console.print(f"  [dim]Cost estimat: ~{len(filtered) * 0.003:.2f} USD[/dim]")

    results: list[dict] = []
    details_req_count = 0
    skipped_with_site = 0

    for place in track(filtered, description="Place Details..."):
        pid = place.get("place_id")
        if not pid:
            continue

        details = get_place_details(api_key, pid)
        details_req_count += 1
        time.sleep(0.05)

        if details.get("business_status") == "CLOSED_PERMANENTLY":
            continue
        if details.get("website"):
            skipped_with_site += 1
            continue

        address = details.get("formatted_address", "")
        if not args.no_filter_county and not is_in_county(address, region["keywords"]):
            continue

        results.append({
            "name": details.get("name", "").strip(),
            "address": address.strip(),
            "phone": details.get("formatted_phone_number", "").strip(),
            "rating": str(place.get("rating", "")),
            "reviews": str(place.get("user_ratings_total", "")),
            "types": ", ".join(place.get("types", [])[:3]),
        })

    results.sort(key=lambda x: x["name"].lower())

    # ── Statistici ───────────────────────────────────────────────────────────
    total_req = nearby_req_count + details_req_count
    console.print(f"\n[bold]Statistici API:[/bold]")
    console.print(f"  Nearby Search requests: {nearby_req_count}")
    console.print(f"  Place Details requests: {details_req_count}")
    console.print(f"  Total requests:         {total_req}")
    console.print(f"  Cu website (excluse):   {skipped_with_site}")
    console.print(f"  Fara website (rezultat):{len(results)}")
    console.print(f"  Cost estimat:           ~${nearby_req_count * 0.032 + details_req_count * 0.003:.2f} USD")

    # ── Salveaza ─────────────────────────────────────────────────────────────
    csv_path = Path(str(output_path) + ".csv")
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["name", "address", "phone", "rating", "reviews", "types"])
        writer.writeheader()
        writer.writerows(results)

    json_path = Path(str(output_path) + ".json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    # ── Afiseaza primele 10 ───────────────────────────────────────────────────
    table = Table(title=f"Firme fara site - {region['name']} (primele 10 din {len(results)})")
    table.add_column("Nume", style="cyan", max_width=35)
    table.add_column("Telefon", style="green", max_width=16)
    table.add_column("Rating", justify="center", max_width=6)
    table.add_column("Adresa", max_width=50)

    for r in results[:10]:
        table.add_row(r["name"], r["phone"] or "-", r["rating"] or "-", r["address"])

    console.print(table)
    console.print(f"\n[green]✓ {len(results)} firme salvate in:[/green]")
    console.print(f"  {csv_path}")
    console.print(f"  {json_path}")

    return str(json_path)


if __name__ == "__main__":
    main()
