"""Genereaza HTML interactiv cu tabel firme + butoane WhatsApp"""

import json
from pathlib import Path
from urllib.parse import quote

import argparse as _ap
_parser = _ap.ArgumentParser(add_help=False)
_parser.add_argument("--input",  default="output/firme_cu_whatsapp.json")
_parser.add_argument("--output", default="")
_parser.add_argument("--title",  default="Firme fără site web — România")
_args, _ = _parser.parse_known_args()

INPUT_JSON  = Path(_args.input)
_out = _args.output or str(INPUT_JSON).replace("firme_cu_whatsapp", "firme_prospectare").replace(".json", ".html")
OUTPUT_HTML = Path(_out)
PAGE_TITLE  = _args.title

def main():
    with open(INPUT_JSON, encoding="utf-8") as f:
        companies = json.load(f)

    cu_link = [c for c in companies if c["whatsapp_link"]]
    fara_tel = [c for c in companies if not c["whatsapp_link"]]

    rows_cu_link = ""
    for i, c in enumerate(cu_link, 1):
        rating_stars = ""
        try:
            r = float(c["rating"])
            full = int(r)
            rating_stars = "★" * full + ("½" if r - full >= 0.5 else "") + f" {c['rating']}"
        except:
            rating_stars = "-"

        type_badge = c["types"].split(",")[0].strip().replace("_", " ") if c["types"] else ""

        rows_cu_link += f"""
        <tr>
          <td class="td-nr">{i}</td>
          <td class="td-name">{c['name']}</td>
          <td class="td-phone">{c['phone']}</td>
          <td class="td-rating">{rating_stars}</td>
          <td class="td-type"><span class="badge">{type_badge}</span></td>
          <td class="td-addr">{c['address']}</td>
          <td class="td-btn">
            <a class="btn-wa" href="{c['whatsapp_link']}" target="_blank">
              <svg viewBox="0 0 24 24" fill="currentColor"><path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347z"/><path d="M12 0C5.373 0 0 5.373 0 12c0 2.123.555 4.116 1.528 5.845L.057 23.5l5.83-1.527A11.95 11.95 0 0012 24c6.627 0 12-5.373 12-12S18.627 0 12 0zm0 22c-1.891 0-3.659-.5-5.189-1.375l-.371-.22-3.862 1.012 1.031-3.76-.242-.387A9.944 9.944 0 012 12C2 6.477 6.477 2 12 2s10 4.477 10 10-4.477 10-10 10z"/></svg>
              Trimite
            </a>
          </td>
        </tr>"""

    rows_fara_tel = ""
    for i, c in enumerate(fara_tel, 1):
        type_badge = c["types"].split(",")[0].strip().replace("_", " ") if c["types"] else ""
        rows_fara_tel += f"""
        <tr>
          <td class="td-nr">{i}</td>
          <td class="td-name">{c['name']}</td>
          <td class="td-phone td-muted">—</td>
          <td class="td-rating">-</td>
          <td class="td-type"><span class="badge">{type_badge}</span></td>
          <td class="td-addr">{c['address']}</td>
          <td class="td-btn"><span class="no-phone">fără telefon</span></td>
        </tr>"""

    html = f"""<!DOCTYPE html>
<html lang="ro">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{PAGE_TITLE}</title>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background: #f0f2f5; color: #1a1a2e; }}

  header {{ background: #1a1a2e; color: #fff; padding: 24px 32px; display: flex; align-items: center; justify-content: space-between; }}
  header h1 {{ font-size: 1.4rem; font-weight: 700; }}
  header p {{ font-size: 0.85rem; opacity: 0.6; margin-top: 4px; }}
  .stats {{ display: flex; gap: 20px; }}
  .stat {{ text-align: center; background: rgba(255,255,255,0.08); border-radius: 10px; padding: 10px 20px; }}
  .stat .n {{ font-size: 1.6rem; font-weight: 800; color: #25d366; }}
  .stat .l {{ font-size: 0.72rem; opacity: 0.6; text-transform: uppercase; letter-spacing: 1px; }}

  .container {{ max-width: 1400px; margin: 0 auto; padding: 28px 20px; }}

  .search-bar {{ margin-bottom: 18px; display: flex; gap: 12px; align-items: center; }}
  .search-bar input {{ flex: 1; padding: 10px 16px; border: 1.5px solid #dde; border-radius: 8px; font-size: 0.95rem; outline: none; transition: border 0.2s; }}
  .search-bar input:focus {{ border-color: #25d366; }}

  .tabs {{ display: flex; gap: 8px; margin-bottom: 18px; }}
  .tab {{ padding: 8px 20px; border-radius: 20px; cursor: pointer; font-size: 0.88rem; font-weight: 600; border: 2px solid transparent; transition: all 0.2s; }}
  .tab.active {{ background: #1a1a2e; color: #fff; }}
  .tab:not(.active) {{ background: #fff; color: #666; border-color: #e0e0e0; }}
  .tab:not(.active):hover {{ border-color: #25d366; color: #25d366; }}

  .panel {{ display: none; }}
  .panel.active {{ display: block; }}

  .table-wrap {{ background: #fff; border-radius: 14px; box-shadow: 0 2px 12px rgba(0,0,0,0.07); overflow: hidden; }}
  table {{ width: 100%; border-collapse: collapse; }}
  thead {{ background: #1a1a2e; color: #fff; }}
  thead th {{ padding: 13px 14px; text-align: left; font-size: 0.78rem; text-transform: uppercase; letter-spacing: 0.8px; font-weight: 600; }}
  tbody tr {{ border-bottom: 1px solid #f0f2f5; transition: background 0.15s; }}
  tbody tr:hover {{ background: #f7fff9; }}
  tbody tr:last-child {{ border-bottom: none; }}
  td {{ padding: 11px 14px; font-size: 0.88rem; vertical-align: middle; }}

  .td-nr {{ color: #aaa; font-size: 0.78rem; width: 40px; }}
  .td-name {{ font-weight: 600; max-width: 220px; }}
  .td-phone {{ font-family: monospace; font-size: 0.85rem; color: #444; white-space: nowrap; }}
  .td-rating {{ color: #f5a623; white-space: nowrap; font-size: 0.82rem; }}
  .td-addr {{ color: #666; font-size: 0.82rem; max-width: 260px; }}
  .td-muted {{ color: #ccc; }}

  .badge {{ background: #eef2ff; color: #4a6cf7; border-radius: 6px; padding: 3px 8px; font-size: 0.75rem; font-weight: 600; white-space: nowrap; }}

  .btn-wa {{ display: inline-flex; align-items: center; gap: 6px; background: #25d366; color: #fff; border-radius: 8px; padding: 7px 14px; text-decoration: none; font-size: 0.82rem; font-weight: 700; transition: background 0.2s, transform 0.1s; white-space: nowrap; }}
  .btn-wa:hover {{ background: #1ebe5d; transform: scale(1.03); }}
  .btn-wa svg {{ width: 16px; height: 16px; }}
  .no-phone {{ color: #ccc; font-size: 0.8rem; font-style: italic; }}

  .count-badge {{ display: inline-block; background: #25d366; color: #fff; border-radius: 10px; padding: 1px 8px; font-size: 0.75rem; margin-left: 6px; }}
  .count-badge.gray {{ background: #ccc; color: #666; }}

  .hidden {{ display: none !important; }}

  @media (max-width: 768px) {{
    header {{ flex-direction: column; gap: 16px; }}
    .stats {{ flex-wrap: wrap; justify-content: center; }}
    .td-addr, .td-type {{ display: none; }}
  }}
</style>
</head>
<body>

<header>
  <div>
    <h1>{PAGE_TITLE}</h1>
    <p>Sursa: Google Maps · generat automat</p>
  </div>
  <div class="stats">
    <div class="stat"><div class="n">{len(companies)}</div><div class="l">Total firme</div></div>
    <div class="stat"><div class="n">{len(cu_link)}</div><div class="l">Cu WhatsApp</div></div>
    <div class="stat"><div class="n">{len(fara_tel)}</div><div class="l">Fără telefon</div></div>
  </div>
</header>

<div class="container">

  <div class="search-bar">
    <input type="text" id="searchInput" placeholder="🔍  Caută după nume, telefon, adresă..." oninput="filterTable()">
  </div>

  <div class="tabs">
    <div class="tab active" onclick="switchTab('cu-tel')">
      Cu telefon <span class="count-badge" id="cnt-cu">{len(cu_link)}</span>
    </div>
    <div class="tab" onclick="switchTab('fara-tel')">
      Fără telefon <span class="count-badge gray" id="cnt-fara">{len(fara_tel)}</span>
    </div>
  </div>

  <div class="panel active" id="panel-cu-tel">
    <div class="table-wrap">
      <table id="table-cu-tel">
        <thead>
          <tr>
            <th>#</th>
            <th>Nume firmă</th>
            <th>Telefon</th>
            <th>Rating</th>
            <th>Categorie</th>
            <th>Adresă</th>
            <th>Acțiune</th>
          </tr>
        </thead>
        <tbody>{rows_cu_link}
        </tbody>
      </table>
    </div>
  </div>

  <div class="panel" id="panel-fara-tel">
    <div class="table-wrap">
      <table id="table-fara-tel">
        <thead>
          <tr>
            <th>#</th>
            <th>Nume firmă</th>
            <th>Telefon</th>
            <th>Rating</th>
            <th>Categorie</th>
            <th>Adresă</th>
            <th></th>
          </tr>
        </thead>
        <tbody>{rows_fara_tel}
        </tbody>
      </table>
    </div>
  </div>

</div>

<script>
  let activeTab = 'cu-tel';

  function switchTab(tab) {{
    activeTab = tab;
    document.querySelectorAll('.tab').forEach((t, i) => {{
      t.classList.toggle('active', (i === 0 && tab === 'cu-tel') || (i === 1 && tab === 'fara-tel'));
    }});
    document.querySelectorAll('.panel').forEach(p => p.classList.remove('active'));
    document.getElementById('panel-' + tab).classList.add('active');
    filterTable();
  }}

  function filterTable() {{
    const q = document.getElementById('searchInput').value.toLowerCase();
    const tableId = 'table-' + activeTab;
    const rows = document.querySelectorAll('#' + tableId + ' tbody tr');
    let visible = 0;
    rows.forEach(row => {{
      const text = row.textContent.toLowerCase();
      const show = !q || text.includes(q);
      row.classList.toggle('hidden', !show);
      if (show) visible++;
    }});
    const countId = activeTab === 'cu-tel' ? 'cnt-cu' : 'cnt-fara';
    document.getElementById(countId).textContent = visible;
  }}
</script>

</body>
</html>"""

    OUTPUT_HTML.write_text(html, encoding="utf-8")
    print(f"HTML generat: {OUTPUT_HTML}")
    print(f"Firme cu WhatsApp: {len(cu_link)}")
    print(f"Firme fara telefon: {len(fara_tel)}")

if __name__ == "__main__":
    main()
