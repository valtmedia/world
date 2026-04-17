#!/usr/bin/env python3
import json
import os
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "config" / "entities.json"
OUTPUT_PATH = ROOT / "data" / "unified-rankings.json"
FALLBACK_PATH = ROOT / "assets" / "fallback-data.js"


def fetch_json(url):
    request = urllib.request.Request(url, headers={"User-Agent": "WorldWealthRank/1.0"})
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def load_config():
    with CONFIG_PATH.open() as file:
        return json.load(file)


def build_countries(config):
    codes = ";".join(config["countryIndicators"])
    url = (
        "https://api.worldbank.org/v2/country/"
        f"{codes}/indicator/NY.GDP.MKTP.CD?format=json&mrnev=1&per_page=300"
    )
    data = fetch_json(url)
    rows = data[1] if isinstance(data, list) and len(data) > 1 else []
    entries = []

    for row in rows:
        value = row.get("value")
        country = row.get("country", {})
        code = row.get("countryiso3code")
        if not value or not country.get("value") or not code:
            continue

        entries.append(
            {
                "name": country["value"],
                "symbol": code,
                "category": "country",
                "metricLabel": "Nominal GDP",
                "valueUsd": round(float(value)),
                "region": "Country",
                "notes": f"World Bank latest annual GDP, {row.get('date')}",
            }
        )

    return entries


def build_crypto(config):
    ids = ",".join(config["cryptoIds"])
    query = urllib.parse.urlencode(
        {
            "vs_currency": "usd",
            "ids": ids,
            "order": "market_cap_desc",
            "per_page": len(config["cryptoIds"]),
            "page": 1,
            "sparkline": "false",
        }
    )
    data = fetch_json(f"https://api.coingecko.com/api/v3/coins/markets?{query}")
    entries = []

    for row in data:
        value = row.get("market_cap")
        if not value:
            continue

        entries.append(
            {
                "name": row["name"],
                "symbol": row["symbol"].upper(),
                "category": "asset",
                "metricLabel": "Market cap",
                "valueUsd": round(float(value)),
                "region": "Global",
                "notes": "CoinGecko crypto market cap",
            }
        )

    return entries


def build_companies(config):
    api_key = os.environ.get("FMP_API_KEY")
    existing_company_names = {
        entry["symbol"]: entry["name"]
        for entry in current_entries_by_category("company")
        if entry.get("symbol") and entry.get("name")
    }

    if not api_key:
        print("FMP_API_KEY missing, keeping company rows from current JSON.", file=sys.stderr)
        return current_entries_by_category("company")

    entries = []
    symbols = config["companySymbols"]
    for symbol in symbols:
        url = f"https://financialmodelingprep.com/api/v3/market-capitalization/{symbol}?apikey={api_key}"
        try:
            data = fetch_json(url)
        except Exception as exc:
            print(f"Company fetch failed for {symbol}: {exc}", file=sys.stderr)
            continue

        if not data:
            continue

        row = data[0]
        market_cap = row.get("marketCap")
        if not market_cap:
            continue

        entries.append(
            {
                "name": row.get("companyName") or existing_company_names.get(symbol) or symbol,
                "symbol": symbol,
                "category": "company",
                "metricLabel": "Market cap",
                "valueUsd": round(float(market_cap)),
                "region": "Public market",
                "notes": "Financial Modeling Prep market cap",
            }
        )
        time.sleep(0.25)

    return entries or current_entries_by_category("company")


def current_entries_by_category(category):
    if not OUTPUT_PATH.exists():
        return []

    with OUTPUT_PATH.open() as file:
        payload = json.load(file)

    return [entry for entry in payload.get("entries", []) if entry.get("category") == category]


def write_outputs(payload):
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n")
    FALLBACK_PATH.write_text(
        "window.WWR_FALLBACK_PAYLOAD = "
        + json.dumps(payload, indent=2, ensure_ascii=False)
        + ";\n"
    )


def main():
    config = load_config()
    manual_assets = config.get("manualAssets", [])
    entries = []
    errors = []

    for builder in (build_countries, build_crypto, build_companies):
        try:
            entries.extend(builder(config))
        except Exception as exc:
            errors.append(f"{builder.__name__}: {exc}")
            print(f"{builder.__name__} failed: {exc}", file=sys.stderr)

    entries.extend(manual_assets)
    entries = [entry for entry in entries if entry.get("valueUsd")]
    entries.sort(key=lambda entry: entry["valueUsd"], reverse=True)

    payload = {
        "updatedAt": datetime.now(timezone.utc).isoformat(),
        "currency": "USD",
        "sourceStatus": "partial" if errors else "ok",
        "sourceErrors": errors,
        "entries": entries,
    }

    write_outputs(payload)
    print(f"Wrote {len(entries)} entries to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
