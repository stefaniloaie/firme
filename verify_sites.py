"""
Verifica daca firmele din firme_fara_site.json au totusi site web
deschizand Google in Playwright si verificand rezultatele reale.

Usage:
    python verify_sites.py              # toate firmele
    python verify_sites.py --limit 20   # primele 20 (test)
    python verify_sites.py --resume     # continua de unde a ramas
"""

import asyncio
import json
import csv
import re
import argparse
import sys
from pathlib import Path
from urllib.parse import urlparse

from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout
from dotenv import load_dotenv
from rich.console import Console
from rich.table import Table

load_dotenv()
console = Console()

INPUT_JSON  = Path("output/firme_fara_site.json")
OUTPUT_CSV  = Path("output/firme_verificate.csv")
OUTPUT_JSON = Path("output/firme_verificate.json")

SKIP_DOMAINS = {
    "google.com", "google.ro", "facebook.com", "instagram.com",
    "youtube.com", "linkedin.com", "twitter.com", "tiktok.com",
    "paginiaurii.ro", "firme.info", "listafirme.ro", "mfax.ro",
    "risco.ro", "dosar.ro", "afaceri.ro", "zelist.ro",
    "olx.ro", "publi24.ro", "tripadvisor.com", "tripadvisor.ro",
    "booking.com", "airbnb.com", "expedia.com",
    "wikipedia.org", "wikimedia.org",
    "anpc.ro", "registrul-comertului.ro", "onrc.ro", "mfinante.ro",
    "imobiliare.ro", "storia.ro", "romimo.ro",
    "yellokki.ro", "bizoo.ro", "merx.ro", "oportunitati.ro",
    "waze.com", "here.com", "openstreetmap.org", "apple.com",
    "reginamaria.ro", "medlife.ro",
}


def is_own_site(url: str) -> tuple[bool, str]:
    try:
        parsed = urlparse(url)
        domain = parsed.netloc.lower().replace("www.", "")
        base = ".".join(domain.split(".")[-2:])
    except Exception:
        return False, ""
    if base in SKIP_DOMAINS or any(sd in domain for sd in SKIP_DOMAINS):
        return False, ""
    return True, f"https://{domain}"


async def accept_cookies(page):
    for text in ["Acceptă tot", "Accept all", "Acceptați tot", "Sunt de acord"]:
        try:
            btn = page.locator(f'button:has-text("{text}")')
            if await btn.count() > 0:
                await btn.first.click()
                await page.wait_for_timeout(800)
                return
        except Exception:
            pass


async def search_on_google(page, name: str, address: str) -> tuple[str, str]:
    city = ""
    for c in ["Bistrița", "Năsăud", "Beclean", "Sângeorz"]:
        if c.lower() in address.lower():
            city = c
            break
    if not city:
        city = "Bistrița"

    query = f"{name} {city}"
    search_url = f"https://www.google.com/search?q={query.replace(' ', '+')}&gl=ro&hl=ro"

    try:
        await page.goto(search_url, wait_until="domcontentloaded", timeout=15000)
        await page.wait_for_timeout(1200)
    except Exception:
        return "EROARE", ""

    # Colecteaza toate link-urile din rezultate organice
    links = await page.eval_on_selector_all(
        "a[href]",
        "els => els.map(e => e.href).filter(h => h.startsWith('http') && !h.includes('google'))"
    )

    for url in links[:15]:
        found, clean_url = is_own_site(url)
        if found:
            return "DA - are site", clean_url

    return "NU - fara site", ""


async def main(limit: int, resume: bool):
    with open(INPUT_JSON, encoding="utf-8") as f:
        companies = json.load(f)

    if limit:
        companies = companies[:limit]

    already_done: set[str] = set()
    existing_results: list[dict] = []

    if resume and OUTPUT_JSON.exists():
        with open(OUTPUT_JSON, encoding="utf-8") as f:
            existing_results = json.load(f)
        already_done = {r["name"] for r in existing_results}
        console.print(f"[yellow]Resume: {len(already_done)} firme deja procesate[/yellow]")

    to_process = [c for c in companies if c["name"] not in already_done]
    results = list(existing_results)
    cu_site = sum(1 for r in results if "DA" in r.get("site_gasit", ""))
    fara_site = sum(1 for r in results if "NU" in r.get("site_gasit", ""))

    console.print(f"[bold]De procesat: {len(to_process)} firme via Google + Playwright[/bold]\n")

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        context = await browser.new_context(
            locale="ro-RO",
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        )
        page = await context.new_page()

        # Accept cookies o singura data
        await page.goto("https://www.google.com/?gl=ro&hl=ro", wait_until="domcontentloaded")
        await page.wait_for_timeout(1000)
        await accept_cookies(page)

        for i, company in enumerate(to_process):
            name    = company["name"]
            address = company["address"]

            nota, site_url = await search_on_google(page, name, address)

            if "DA" in nota:
                cu_site += 1
                icon = "[green]✓[/green]"
            elif "NU" in nota:
                fara_site += 1
                icon = "[red]✗[/red]"
            else:
                icon = "[yellow]![/yellow]"

            results.append({**company, "site_gasit": nota, "site_url": site_url})

            console.print(
                f"  {icon} [{i+1}/{len(to_process)}] {name[:38]:<38} | {nota} | [dim]{site_url[:45]}[/dim]",
                highlight=False,
            )

            # Salveaza progres la fiecare 25
            if (i + 1) % 25 == 0:
                _save(results)
                console.print(
                    f"  [green]↳ Salvat ({len(results)} procesate | cu_site={cu_site} | fara={fara_site})[/green]"
                )

            await page.wait_for_timeout(800)

        await browser.close()

    _save(results)

    console.print(f"\n[bold]REZULTATE FINALE:[/bold]")
    console.print(f"  [red]Au site (fals pozitive Places API): {cu_site}[/red]")
    console.print(f"  [green]Confirmat FARA site:               {fara_site}[/green]")

    confirmed = [r for r in results if "NU" in r.get("site_gasit", "")]
    table = Table(title=f"Firme confirmate FARA site ({len(confirmed)} total)")
    table.add_column("#",      style="dim",  max_width=4)
    table.add_column("Nume",   style="cyan", max_width=35)
    table.add_column("Telefon",style="green",max_width=14)
    table.add_column("Rating", justify="center", max_width=6)
    table.add_column("Nota",   max_width=18)
    table.add_column("Adresa", max_width=40)

    for idx, r in enumerate(confirmed[:30], 1):
        table.add_row(
            str(idx), r["name"], r["phone"] or "-",
            r["rating"] or "-", r["site_gasit"], r["address"][:40]
        )

    console.print(table)
    console.print(f"\n[green]✓ Salvat in:[/green] {OUTPUT_CSV} / {OUTPUT_JSON}")


def _save(results: list[dict]):
    OUTPUT_CSV.parent.mkdir(exist_ok=True)
    fieldnames = ["name", "address", "phone", "rating", "reviews", "types", "site_gasit", "site_url"]
    with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)
    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit",  type=int, default=0)
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()
    asyncio.run(main(args.limit, args.resume))
