"""
Genereaza link-uri WhatsApp pre-completate cu mesajul de prospectare
pentru fiecare firma cu telefon din firme_fara_site.json
"""

import json
import csv
from urllib.parse import quote
from pathlib import Path

import argparse as _ap
_parser = _ap.ArgumentParser(add_help=False)
_parser.add_argument("--input",  default="output/firme_fara_site.json")
_parser.add_argument("--output", default="")
_args, _ = _parser.parse_known_args()

INPUT_JSON  = Path(_args.input)
_out_prefix = _args.output or str(INPUT_JSON).replace("firme_fara_site", "firme_cu_whatsapp").replace(".json", "")
OUTPUT_CSV  = Path(_out_prefix + ".csv")
OUTPUT_JSON = Path(_out_prefix + ".json")

MESAJ = """Buna ziua,

Am observat ca nu aveti un site web (cel putin pe Google Maps) si m-ar interesa daca credeti ca ati avea nevoie si ati vrea sa colaboram in acest sens.

Pretul este undeva intre 150-200 euro in functie de complexitate, dar nu trebuie sa platiti nimic pana nu vedeti site-ul web live. Va pot face gratuit si un demo cu un template pentru specificul dvs.

Recent am facut in zona: https://pensiuneaclarisia.ro/

Astept raspunsul dvs in caz de interes.

Multumesc,"""


def clean_phone(phone: str) -> str:
    """Transforma numarul in format international pentru WhatsApp."""
    digits = "".join(c for c in phone if c.isdigit())
    if not digits:
        return ""
    # Romania: 07xx -> +407xx
    if digits.startswith("07") or digits.startswith("02") or digits.startswith("03"):
        return "40" + digits
    # Deja cu prefix
    if digits.startswith("40"):
        return digits
    return digits


def whatsapp_link(phone: str, message: str) -> str:
    phone_clean = clean_phone(phone)
    if not phone_clean:
        return ""
    encoded = quote(message)
    return f"https://wa.me/{phone_clean}?text={encoded}"


def main():
    with open(INPUT_JSON, encoding="utf-8") as f:
        companies = json.load(f)

    results = []
    cu_link = 0
    fara_telefon = 0

    for c in companies:
        phone = c.get("phone", "").strip()
        link = whatsapp_link(phone, MESAJ) if phone else ""

        if link:
            cu_link += 1
        else:
            fara_telefon += 1

        results.append({
            "name": c["name"],
            "address": c["address"],
            "phone": phone,
            "rating": c.get("rating", ""),
            "reviews": c.get("reviews", ""),
            "types": c.get("types", ""),
            "whatsapp_link": link,
        })

    # CSV
    with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["name", "address", "phone", "rating", "reviews", "types", "whatsapp_link"]
        )
        writer.writeheader()
        writer.writerows(results)

    # JSON
    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"Total firme:         {len(results)}")
    print(f"Cu link WhatsApp:    {cu_link}")
    print(f"Fara telefon:        {fara_telefon}")
    print(f"\nFisiere generate:")
    print(f"  {OUTPUT_CSV}")
    print(f"  {OUTPUT_JSON}")

    # Preview primele 5 cu link
    print("\nExemple:")
    for r in [x for x in results if x["whatsapp_link"]][:5]:
        print(f"  {r['name']}")
        print(f"    Tel:       {r['phone']}")
        print(f"    WhatsApp:  {r['whatsapp_link'][:80]}...")
        print()


if __name__ == "__main__":
    main()
