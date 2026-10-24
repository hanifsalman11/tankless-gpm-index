import os
import json
import re
import time
import urllib.request
import urllib.parse
from datetime import datetime, timezone

# ==========================================
# ENVIRONMENT CONFIGURATION
# ==========================================
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "").strip()
SITE_BASE_URL = os.environ.get("SITE_BASE_URL", "https://hanifsalman11.github.io/tankless-gpm-index").rstrip("/")
INDEXNOW_KEY = os.environ.get("INDEXNOW_KEY", "e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0").strip()
CUSTOM_HEATER = os.environ.get("CUSTOM_HEATER", "").strip()
PAGES_PER_RUN = int(os.environ.get("PAGES_PER_RUN", "3"))

DOCS_DIR = "docs"
DATA_DIR = "data"
PUBLISHED_FILE = os.path.join(DATA_DIR, "published_heaters.json")
MONETIZATION_FILE = os.path.join(DATA_DIR, "monetization.json")

# Format: (Model / Home Scenario, Fuel Type, Power Rating [BTU or kW], Thermal Efficiency, Utility Spec, Max Rated GPM)
SEED_HEATERS = [
    ("Rinnai RU199iN SENSEI Super High Efficiency Plus", "Natural Gas", 199000, 0.96, "3/4\" Gas Line + 120V 15A", 11.0),
    ("Navien NPE-240A2 Condensing Recirculating Tankless", "Natural Gas / LP", 199900, 0.96, "3/4\" Gas Line + 2\" PVC Vent", 11.2),
    ("Navien NPE-180A2 Condensing Tankless Water Heater", "Natural Gas / LP", 150000, 0.96, "3/4\" Gas Line + 2\" PVC Vent", 8.4),
    ("Rinnai RXP199iN Built-In Recirculation Pump Tankless", "Natural Gas", 199000, 0.97, "3/4\" Gas Line + 2\" PVC Vent", 11.1),
    ("Rinnai RL94iN High-Efficiency Non-Condensing", "Natural Gas", 199000, 0.83, "3/4\" Gas Line + Concentric Vent", 9.8),
    ("Rinnai V65iN 6.5 GPM Indoor Tankless Water Heater", "Natural Gas", 150000, 0.82, "3/4\" Gas Line + Concentric Vent", 6.5),
    ("EcoSmart ECO 27 (27kW 240V) Electric Tankless", "240V Electric", 27, 0.99, "3x 40A Double-Pole Breakers (3x 8 AWG)", 5.3),
    ("EcoSmart ECO 18 (18kW 240V) Electric Tankless", "240V Electric", 18, 0.99, "2x 40A Double-Pole Breakers (2x 8 AWG)", 3.6),
    ("EcoSmart ECO 36 (36kW 240V) Whole-Home Electric", "240V Electric", 36, 0.99, "4x 40A Double-Pole Breakers (4x 8 AWG)", 7.1),
    ("Stiebel Eltron Tempra 24 Plus Advanced Flow Control", "240V Electric", 24, 0.99, "2x 50A Double-Pole Breakers (2x 8 AWG)", 4.8),
    ("Stiebel Eltron Tempra 29 Plus Whole-House Electric", "240V Electric", 29, 0.99, "3x 40A Double-Pole Breakers (3x 8 AWG)", 5.7),
    ("Stiebel Eltron Tempra 36 Plus Cold-Climate Electric", "240V Electric", 36, 0.99, "3x 50A Double-Pole Breakers (3x 8 AWG)", 7.2),
    ("Rheem RTGH-95DVLN-3 Prestige Condensing Tankless", "Natural Gas", 199900, 0.95, "3/4\" Gas Line + 2\" PVC Vent", 9.5),
    ("Rheem RTEX-24 (24kW 240V) Professional Classic Electric", "240V Electric", 24, 0.99, "3x 40A Double-Pole Breakers (3x 8 AWG)", 4.8),
    ("Rheem RTEX-18 (18kW 240V) Tankless Electric", "240V Electric", 18, 0.99, "2x 40A Double-Pole Breakers (2x 8 AWG)", 3.6),
    ("Noritz EZ111DV Condensing Top-Mount Replacement", "Natural Gas", 199900, 0.96, "3/4\" Gas Line + 2\" Flex Vent", 11.1),
    ("Noritz NRC66DVN 6.6 GPM Condensing Tankless", "Natural Gas", 120000, 0.93, "1/2\" or 3/4\" Gas Line", 6.6),
    ("Takagi T-H3-DV-N Condensing 10.0 GPM Tankless", "Natural Gas", 199000, 0.95, "3/4\" Gas Line + 3\" PVC Vent", 10.0),
    ("A.O. Smith ATI-540H-N Condensing 10.0 GPM Tankless", "Natural Gas", 199000, 0.95, "3/4\" Gas Line + 2\" PVC Vent", 10.0),
    ("Bradford White Infiniti K Series 199,000 BTU", "Natural Gas", 199000, 0.96, "3/4\" Gas Line + 2\" PVC Vent", 10.6),
    ("Bosch Greentherm T9900i SE 199k BTU WiFi Tankless", "Natural Gas", 199000, 0.96, "3/4\" Gas Line + 2\" PVC Vent", 10.6),
    ("Marey GA16LP 4.3 GPM Liquid Propane Tankless", "Liquid Propane", 115000, 0.84, "3/4\" LP Gas Line", 4.3),
    ("Camplux BD264 2.64 GPM Off-Grid Outdoor Propane", "Liquid Propane", 68000, 0.82, "Standard 20lb Propane Regulator", 2.6),
    ("2-Bathroom Home Tankless Water Heater Sizing", "Natural Gas / LP", 160000, 0.95, "3/4\" Gas Line (6.5–8.0 GPM)", 8.0),
    ("3-Bathroom Family Home Tankless Water Heater Sizing", "Natural Gas / LP", 199000, 0.96, "3/4\" Gas Line (9.5–11.0 GPM)", 10.5),
    ("4-Bathroom Large Estate Dual-Cascade Tankless Sizing", "Natural Gas / LP", 199900, 0.96, "1\" Gas Header + Common Vent", 11.2),
    ("Northern Cold Groundwater (40°F Inlet / 80°F Rise) Sizing", "Natural Gas", 199900, 0.96, "3/4\" Gas Line Condensing", 11.0),
    ("Southern Warm Groundwater (68°F Inlet / 52°F Rise) Sizing", "Natural Gas / Electric", 160000, 0.95, "3/4\" Gas or 24kW Electric", 8.5),
    ("Radiant Floor Hydronic Heating + DHW Combo Tankless", "Natural Gas", 199900, 0.96, "3/4\" Gas + Air Handler Loop", 11.0),
    ("RV & Tiny Cabin On-Demand 55,000 BTU Propane Heater", "Liquid Propane", 55000, 0.85, "12V DC Igniter + LP Gas", 2.9)
]


def load_json(filepath, default):
    if os.path.exists(filepath):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"[WARN] Could not parse {filepath}: {e}")
    return default


def save_json(filepath, data):
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def slugify(text):
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9\s-]", "", text)
    return re.sub(r"[\s-]+", "-", text).strip("-")


def safe_float(val, default=199000.0):
    try:
        cleaned = re.sub(r"[^0-9.]", "", str(val))
        return float(cleaned) if cleaned else float(default)
    except Exception:
        return float(default)


def build_amazon_url(search_keywords, mon_cfg):
    domain = mon_cfg.get("marketplace_domain", "www.amazon.com")
    tag = mon_cfg.get("amazon_associate_tag", "YOUR_AMAZON_TAG-20")
    encoded_q = urllib.parse.quote_plus(search_keywords)
    return f"https://{domain}/s?k={encoded_q}&tag={tag}"


def discover_google_tankless_queries():
    """Mengambil kueri kalkulator GPM & ukuran Tankless Water Heater dari Google Autocomplete US."""
    discovered = []
    seeds = [
        "what size tankless water heater for ",
        "rinnai tankless ",
        "navien npe ",
        "ecosmart electric tankless "
    ]
    for seed in seeds:
        try:
            url = f"http://suggestqueries.google.com/complete/search?client=firefox&hl=en&gl=us&q={urllib.parse.quote(seed)}"
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=8) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                for suggestion in data[1]:
                    cleaned = suggestion.lower()
                    for pref in seeds:
                        cleaned = cleaned.replace(pref, "")
                    cleaned = re.sub(
                        r"\b(calculator|size|sizing|chart|manual|review|reddit|for)\b",
                        "",
                        cleaned
                    ).strip()
                    if 5 <= len(cleaned) <= 42:
                        is_elec = "electric" in suggestion.lower() or "ecosmart" in suggestion.lower() or "kw" in suggestion.lower()
                        if is_elec:
                            discovered.append((cleaned.title(), "240V Electric", 27, 0.99, "3x 40A Breakers (8 AWG)", 5.3))
                        else:
                            discovered.append((cleaned.title(), "Natural Gas / LP", 199000, 0.96, "3/4\" Gas Line + 2\" PVC Vent", 10.5))
        except Exception as e:
            print(f"[WARN] Google Suggest notice: {e}")
    return discovered


def build_deterministic_tankless_data(heater_tuple):
    """Mesin Fisika Kalorimetri Air Panas (Delta-T) & Kelistrikan/Gas (100% bebas gagal)."""
    model_name, fuel_type, power_val, eff, util_spec, max_gpm = heater_tuple

    is_electric = power_val <= 100
    # Rumus Kalorimetri:
    # Effective BTU/hr = (kW * 3412 * eff) untuk elektrik, atau (BTU * eff) untuk gas
    effective_btu_hr = (power_val * 3412.14 * eff) if is_electric else (power_val * eff)

    # GPM pada Kenaikan Suhu Musim Panas/Selatan (50°F Delta-T: 70°F inlet -> 120°F outlet)
    gpm_50f_rise = round(effective_btu_hr / (500.0 * 50.0), 1)
    # GPM pada Kenaikan Suhu Musim Dingin/Utara (75°F Delta-T: 45°F inlet -> 120°F outlet)
    gpm_75f_rise = round(effective_btu_hr / (500.0 * 75.0), 1)

    showers_winter = max(1, int(gpm_75f_rise // 2.0))
    showers_summer = max(1, int(gpm_50f_rise // 2.0))
    power_label = f"{int(power_val)} kW ({int(round(power_val * 1000 / 240))}A @ 240V)" if is_electric else f"{int(power_val):,} BTU/hr"

    return {
        "heater_name": model_name,
        "fuel_type": fuel_type,
        "seo_title": f"{model_name} GPM Flow Rate, Temp Rise (ΔT) & Sizing Calculator (2026)",
        "meta_description": f"Calculate exact hot water GPM flow rate ({gpm_50f_rise} GPM summer / {gpm_75f_rise} GPM winter), simultaneous showers ({showers_winter}–{showers_summer}), and utility sizing for {model_name}.",
        "specs": {
            "fuel_type": fuel_type,
            "power_rating": power_val,
            "power_label": power_label,
            "thermal_efficiency": eff,
            "utility_requirement": util_spec,
            "max_rated_gpm": max_gpm,
            "gpm_at_50f_rise": gpm_50f_rise,
            "gpm_at_75f_rise": gpm_75f_rise
        },
        "thermodynamic_verdict": f"Rated at {power_label} with {int(eff*100)}% thermal efficiency ({fuel_type}), the {model_name} delivers {gpm_50f_rise} GPM at a moderate 50°F temperature rise (supporting ~{showers_summer} simultaneous 2.0-GPM showers) and {gpm_75f_rise} GPM during a freezing 75°F winter temperature rise (~{showers_winter} simultaneous showers). Proper installation requires {util_spec} plus a 3/4-inch brass isolation service valve kit.",
        "hardware_bundle": [
            {
                "badge": f"{power_label} Unit",
                "title": f"{model_name} On-Demand Tankless Water Heater",
                "price_range": "$449 - $1,699",
                "amazon_query": f"{model_name} Tankless Water Heater",
                "plumb_note": f"Modulates output dynamically based on flow sensor demand at {int(eff*100)}% energy efficiency."
            },
            {
                "badge": "3/4\" Isolation Valve Kit",
                "title": "3/4-Inch Lead-Free Forged Brass Tankless Isolation Service Valve Kit + 150 PSI Relief Valve",
                "price_range": "$54 - $99",
                "amazon_query": "3/4 Inch Brass Tankless Water Heater Isolation Service Valve Kit",
                "plumb_note": "Color-coded red/blue quarter-turn purge ports allow you to isolate and flush the heat exchanger in 5 minutes without cutting pipes."
            },
            {
                "badge": "Descaling Flush Pump Kit",
                "title": "1/6 HP Submersible Tankless Descaling Pump, 6ft Stainless Hoses, Bucket & Descaler Kit",
                "price_range": "$74 - $139",
                "amazon_query": "Tankless Water Heater Flushing Kit Submersible Pump Descaler",
                "plumb_note": "Annual 45-minute descaling circulation removes calcium carbonate scale buildup to protect your 12-to-15 year heat exchanger warranty."
            },
            {
                "badge": "Anti-Scale Inline Filter",
                "title": "3/4\" NPT Whole-House Tankless Scale Inhibitor Polyphosphate System (6-Month Cartridge)",
                "price_range": "$64 - $149",
                "amazon_query": "Tankless Water Heater Anti Scale Filter System 3/4 NPT",
                "plumb_note": "Coats dissolved calcium and magnesium ions before they enter the copper/stainless heat exchanger coils."
            }
        ],
        "plumbing_checklist": [
            f"Verify your incoming winter groundwater temperature: a 120°F shower with 45°F winter inlet water requires a 75°F temperature rise (ΔT), reducing flow to {gpm_75f_rise} GPM.",
            f"Install {util_spec} per manufacturer & National Fuel Gas Code (NFPA 54) / NEC rules; undersized 1/2\" gas lines or undersized wire gauges cause flame-outs and error codes under peak load.",
            "Thread a 3/4-inch Lead-Free Brass Isolation Service Valve set directly onto the hot and cold nipples during initial install so annual vinegar/citric-acid flushing requires zero plumbing disassembly.",
            "Flush the heat exchanger once every 12 months using a submersible descaling pump and 4 gallons of food-grade citric acid descaler to prevent flow-restrictor screen blockages."
        ],
        "faqs": [
            {
                "q": f"How many showers can the {model_name} run at the same time?",
                "a": f"Standard modern showerheads use 2.0 GPM. In warm southern climates (50°F temperature rise), the {model_name} delivers {gpm_50f_rise} GPM—enough for {showers_summer} simultaneous showers plus a faucet. In freezing northern winters (75°F temperature rise), output is {gpm_75f_rise} GPM ({showers_winter} simultaneous showers)."
            },
            {
                "q": f"How do you calculate GPM for the {model_name} at any groundwater temperature?",
                "a": f"Use the thermodynamic heat-transfer formula: GPM = ({int(effective_btu_hr):,} Effective BTU/hr) ÷ (500 × ΔT), where ΔT is Target Hot Water Temp (120°F) minus Incoming Groundwater Temp."
            },
            {
                "q": f"What gas line or electrical breaker is required for the {model_name}?",
                "a": f"The {model_name} requires {util_spec} along with a dedicated 3/4-inch cold water supply and 150 PSI / 200,000 BTU ASME temperature-and-pressure (T&P) relief valve."
            }
        ]
    }


def generate_tankless_data(heater_tuple):
    """Memanggil Gemini 2.5 Flash API; jika gagal otomatis memakai Deterministic Delta-T Engine."""
    if not GEMINI_API_KEY:
        return build_deterministic_tankless_data(heater_tuple)

    model_name, fuel_type, power_val, eff, util_spec, max_gpm = heater_tuple
    is_electric = power_val <= 100
    eff_btu = (power_val * 3412.14 * eff) if is_electric else (power_val * eff)
    gpm_50 = round(eff_btu / (500.0 * 50.0), 1)
    gpm_75 = round(eff_btu / (500.0 * 75.0), 1)
    p_label = f"{int(power_val)} kW" if is_electric else f"{int(power_val):,} BTU/hr"

    prompt = f"""
You are a Master Licensed Plumber & Hydronic Thermal Engineer. Create an accurate 2026 GPM flow rate, temperature rise (Delta-T), and installation sizing guide for: "{model_name}".
Baseline reference specs: Fuel={fuel_type}, Power={p_label}, Thermal Efficiency={int(eff*100)}%, Utility Spec={util_spec}, Max Rated Flow={max_gpm} GPM, Flow @ 50F Rise={gpm_50} GPM, Flow @ 75F Winter Rise={gpm_75} GPM.
Return ONLY a valid JSON object matching this exact schema:
{{
  "heater_name": "{model_name}",
  "fuel_type": "{fuel_type}",
  "seo_title": "{model_name} GPM Flow Rate, Temp Rise (ΔT) & Sizing Calculator (2026)",
  "meta_description": "Calculate exact hot water GPM flow rate by groundwater temperature, simultaneous showers, and gas/breaker sizing for {model_name}.",
  "specs": {{
    "fuel_type": "{fuel_type}",
    "power_rating": {power_val},
    "power_label": "{p_label}",
    "thermal_efficiency": {eff},
    "utility_requirement": "{util_spec}",
    "max_rated_gpm": {max_gpm},
    "gpm_at_50f_rise": {gpm_50},
    "gpm_at_75f_rise": {gpm_75}
  }},
  "thermodynamic_verdict": "3-sentence technical summary stating BTU/kW rating, efficiency, exact GPM at 50F rise vs 75F winter rise, and required gas line or electrical breaker.",
  "hardware_bundle": [
    {{
      "badge": "Tankless Heater Unit",
      "title": "{model_name}",
      "price_range": "$449 - $1,699",
      "amazon_query": "{model_name} Tankless Water Heater",
      "plumb_note": "1-sentence modulation and efficiency note"
    }},
    {{
      "badge": "3/4\" Brass Service Valves",
      "title": "3/4-Inch Lead-Free Brass Tankless Isolation Service Valve Kit + 150 PSI Relief Valve",
      "price_range": "$54 - $99",
      "amazon_query": "3/4 Inch Brass Tankless Water Heater Isolation Valve Kit",
      "plumb_note": "1-sentence purge port and relief valve note"
    }},
    {{
      "badge": "Descaling Flush Pump Kit",
      "title": "Submersible Descaling Pump, Stainless Hoses, Bucket & Citric Acid Flush Kit",
      "price_range": "$74 - $139",
      "amazon_query": "Tankless Water Heater Flushing Kit Pump Descaler",
      "plumb_note": "1-sentence scale removal and warranty protection note"
    }},
    {{
      "badge": "Anti-Scale Pre-Filter",
      "title": "3/4\" NPT Inline Tankless Water Heater Scale Inhibitor Filter System",
      "price_range": "$64 - $149",
      "amazon_query": "Tankless Water Heater Scale Inhibitor Filter 3/4",
      "plumb_note": "1-sentence heat exchanger scale prevention note"
    }}
  ],
  "plumbing_checklist": [
    "Step 1 regarding winter groundwater temperature and Delta-T flow reduction",
    "Step 2 regarding gas pipe diameter (3/4 inch) or multi-pole 240V breaker sizing",
    "Step 3 regarding 3/4-inch brass isolation service valve installation",
    "Step 4 regarding annual 45-minute submersible pump descaling flush"
  ],
  "faqs": [
    {{"q": "How many showers can the {model_name} run at once?", "a": "Exact GPM and simultaneous fixtures in summer vs winter."}},
    {{"q": "How does groundwater temperature affect the {model_name}?", "a": "Exact Delta-T formula and GPM output numbers."}},
    {{"q": "What gas line or breaker size is needed for the {model_name}?", "a": "Exact pipe size, venting, or 240V breaker/wire AWG spec."}}
  ]
}}
"""

    for model_id in ["gemini-2.5-flash", "gemini-2.0-flash"]:
        try:
            endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/{model_id}:generateContent?key={GEMINI_API_KEY}"
            payload = {
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {
                    "temperature": 0.2,
                    "responseMimeType": "application/json"
                }
            }
            req = urllib.request.Request(
                endpoint,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=35) as resp:
                result = json.loads(resp.read().decode("utf-8"))
                raw_text = result["candidates"][0]["content"]["parts"][0]["text"].strip()
                raw_text = re.sub(r"^```(?:json)?\s*", "", raw_text)
                raw_text = re.sub(r"\s*```$", "", raw_text)
                parsed = json.loads(raw_text)
                if "specs" in parsed and "hardware_bundle" in parsed:
                    return parsed
        except Exception as e:
            print(f"[WARN] Gemini ({model_id}) notice for '{model_name}': {e}")

    return build_deterministic_tankless_data(heater_tuple)


def build_tankless_html_page(data, slug, mon_cfg):
    heater_name = data.get("heater_name", "Tankless Water Heater")
    sp = data.get("specs", {})
    fuel_type = sp.get("fuel_type", "Natural Gas")
    power_val = safe_float(sp.get("power_rating", 199000), 199000)
    is_elec = power_val <= 100
    power_label = sp.get("power_label", f"{int(power_val)} kW" if is_elec else f"{int(power_val):,} BTU/hr")
    eff = round(safe_float(sp.get("thermal_efficiency", 0.96), 0.96), 2)
    util_spec = sp.get("utility_requirement", "3/4\" Gas Line + 2\" PVC Vent")
    gpm_50 = round(safe_float(sp.get("gpm_at_50f_rise", 7.6), 7.6), 1)
    gpm_75 = round(safe_float(sp.get("gpm_at_75f_rise", 5.1), 5.1), 1)

    eff_btu_total = int(round((power_val * 3412.14 * eff) if is_elec else (power_val * eff)))

    header_cta = mon_cfg.get("header_cta", {})
    header_cta_url = build_amazon_url(header_cta.get("search_query", "Tankless+Water+Heater+199000+BTU"), mon_cfg)

    schema_graph = {
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "SoftwareApplication",
                "name": f"{heater_name} GPM Flow Rate & Temperature Rise Calculator",
                "applicationCategory": "UtilitiesApplication",
                "operatingSystem": "Web Browser",
                "offers": {"@type": "Offer", "price": "0", "priceCurrency": "USD"}
            },
            {
                "@type": "FAQPage",
                "mainEntity": [
                    {
                        "@type": "Question",
                        "name": f.get("q", ""),
                        "acceptedAnswer": {"@type": "Answer", "text": f.get("a", "")}
                    } for f in data.get("faqs", [])
                ]
            }
        ]
    }

    bundle_html = ""
    for item in data.get("hardware_bundle", []):
        amz_url = build_amazon_url(item.get("amazon_query", item.get("title", "Tankless Water Heater")), mon_cfg)
        bundle_html += f"""
        <div class="bg-slate-900 border border-slate-800 rounded-xl p-5 flex flex-col justify-between hover:border-rose-500/60 transition">
          <div>
            <div class="flex items-center justify-between gap-2 mb-2">
              <span class="text-xs font-bold uppercase tracking-wider bg-rose-500/10 text-rose-400 border border-rose-500/20 px-2.5 py-0.5 rounded">{item.get('badge', 'Plumbing Gear')}</span>
              <span class="text-sm font-bold text-emerald-400">{item.get('price_range', '$59+')}</span>
            </div>
            <h3 class="text-base font-bold text-white mt-2">{item.get('title', '')}</h3>
            <p class="text-xs text-slate-400 mt-2 leading-relaxed">🔥 {item.get('plumb_note', '')}</p>
          </div>
          <a href="{amz_url}" target="_blank" rel="nofollow sponsored" class="mt-5 block text-center bg-rose-500 hover:bg-rose-400 text-white font-extrabold py-2.5 px-4 rounded-lg text-sm transition shadow-lg">
            Check Price on Amazon →
          </a>
        </div>"""

    # Build Temperature Rise (Delta-T) vs GPM Flow Matrix Table
    matrix_rows_html = ""
    for in_temp, zone_label in [
        (72, "72°F Inlet (South FL / TX Summer)"),
        (62, "62°F Inlet (CA / Southeast Average)"),
        (52, "52°F Inlet (Mid-Atlantic / PNW)"),
        (42, "42°F Inlet (Midwest / Northeast Winter)"),
        (37, "37°F Inlet (Upper North / Mountain Freeze)")
    ]:
        delta_t = 120 - in_temp
        gpm_calc = round(eff_btu_total / (500.0 * delta_t), 1)
        shw_cnt = round(gpm_calc / 2.0, 1)
        matrix_rows_html += f"""
        <tr class="border-b border-slate-800 hover:bg-slate-800/40">
          <td class="py-3 px-4 font-bold text-white">{zone_label}</td>
          <td class="py-3 px-4 text-rose-400 font-semibold">+{delta_t}°F Rise (to 120°F)</td>
          <td class="py-3 px-4 font-bold text-emerald-400">{gpm_calc} GPM Continuous</td>
          <td class="py-3 px-4 text-xs text-slate-300">~{shw_cnt} Showers (2.0 GPM ea)</td>
        </tr>"""

    checklist_html = ""
    for idx, step_text in enumerate(data.get("plumbing_checklist", []), start=1):
        checklist_html += f"""
        <label class="flex items-start gap-3.5 bg-slate-900 border border-slate-800 rounded-xl p-4 cursor-pointer hover:border-slate-700 transition">
          <input type="checkbox" class="mt-1 w-5 h-5 accent-rose-500 rounded cursor-pointer tank-check">
          <span class="text-sm text-slate-200 leading-relaxed"><strong>Plumbing Step {idx}:</strong> {step_text}</span>
        </label>"""

    faqs_html = "".join([
        f"<div class='bg-slate-900 border border-slate-800 rounded-xl p-5'><h3 class='font-bold text-white text-base mb-2'>{f.get('q', '')}</h3><p class='text-sm text-slate-300 leading-relaxed'>{f.get('a', '')}</p></div>"
        for f in data.get("faqs", [])
    ])

    canonical_url = f"{SITE_BASE_URL}/{slug}.html"
    amz_domain = mon_cfg.get("marketplace_domain", "www.amazon.com")
    amz_tag = mon_cfg.get("amazon_associate_tag", "YOUR_AMAZON_TAG-20")

    html = f"""<!DOCTYPE html>
<html lang="en" class="dark">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{data.get('seo_title', heater_name)}</title>
  <meta name="description" content="{data.get('meta_description', '')}">
  <link rel="canonical" href="{canonical_url}">
  <meta property="og:title" content="{data.get('seo_title', heater_name)}">
  <meta property="og:description" content="{data.get('meta_description', '')}">
  <meta property="og:type" content="article">
  <meta property="og:url" content="{canonical_url}">
  <script src="https://cdn.tailwindcss.com"></script>
  <script type="application/ld+json">{json.dumps(schema_graph)}</script>
</head>
<body class="bg-slate-950 text-slate-100 antialiased min-h-screen flex flex-col">
  <header class="border-b border-slate-800 bg-slate-900/80 backdrop-blur sticky top-0 z-30">
    <div class="max-w-5xl mx-auto px-4 py-3.5 flex items-center justify-between">
      <a href="index.html" class="text-lg font-black tracking-tight text-white flex items-center gap-2">
        <span class="bg-rose-500 text-white px-2 py-0.5 rounded font-black">TANKLESS</span>GPMIndex
      </a>
      <a href="{header_cta_url}" target="_blank" rel="nofollow sponsored" class="text-xs sm:text-sm bg-rose-500 hover:bg-rose-400 text-white font-extrabold px-3.5 py-2 rounded-lg transition">
        {header_cta.get('cta_text', 'Shop Tankless Water Heaters →')}
      </a>
    </div>
  </header>

  <main class="max-w-5xl mx-auto px-4 py-10 flex-1 w-full">
    <div class="mb-8">
      <div class="flex flex-wrap items-center gap-2.5 mb-3">
        <span class="text-xs font-extrabold uppercase tracking-widest bg-rose-500 text-white px-3 py-1 rounded-full">{power_label} ({int(eff*100)}% Eff)</span>
        <span class="text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 px-3 py-1 rounded-full">50°F Rise: {gpm_50} GPM | 75°F Rise: {gpm_75} GPM</span>
        <span class="text-xs font-semibold bg-slate-800 text-slate-300 px-3 py-1 rounded-full">{fuel_type} | {util_spec}</span>
      </div>
      <h1 class="text-3xl sm:text-4xl font-black text-white leading-tight">{data.get('seo_title', heater_name)}</h1>
      <div class="mt-4 bg-slate-900 border-l-4 border-rose-500 p-4 rounded-r-xl text-sm text-slate-200 leading-relaxed">
        <strong>Master Plumber ΔT Sizing Verdict:</strong> {data.get('thermodynamic_verdict', '')}
      </div>
    </div>

    <!-- INTERACTIVE TEMPERATURE RISE (DELTA-T), GPM & SIMULTANEOUS FIXTURE CALCULATOR -->
    <section class="bg-slate-900 border border-slate-800 rounded-2xl p-6 sm:p-8 mb-12 shadow-2xl">
      <h2 class="text-xl font-extrabold text-white mb-2">Interactive {heater_name} ΔT Flow & Shower Calculator</h2>
      <p class="text-xs text-slate-400 mb-6">Adjust your incoming winter groundwater temperature, target hot water temperature, and active bathroom/kitchen fixtures to verify whether this unit can keep up without cold-water sandwich drops.</p>

      <div class="grid md:grid-cols-2 gap-8 items-center">
        <div class="space-y-5">
          <div>
            <div class="flex justify-between text-sm font-medium mb-1.5">
              <label for="inletSlider" class="text-slate-300">Incoming Winter Groundwater Temp (°F)</label>
              <span class="text-rose-400 font-bold"><span id="inletVal">50</span>°F Inlet</span>
            </div>
            <input id="inletSlider" type="range" min="35" max="78" step="1" value="50" class="w-full accent-rose-500 cursor-pointer">
          </div>

          <div>
            <div class="flex justify-between text-sm font-medium mb-1.5">
              <label for="targetSlider" class="text-slate-300">Target Hot Water Setpoint (°F)</label>
              <span class="text-rose-400 font-bold"><span id="targetVal">120</span>°F Setpoint</span>
            </div>
            <input id="targetSlider" type="range" min="105" max="140" step="5" value="120" class="w-full accent-rose-500 cursor-pointer">
          </div>

          <div class="grid grid-cols-2 gap-3">
            <div>
              <label for="showerSelect" class="block text-xs font-medium text-slate-400 mb-1">Active Showers (2.0 GPM ea)</label>
              <select id="showerSelect" class="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-rose-500">
                <option value="2.0">1 Shower (2.0 GPM)</option>
                <option value="4.0" selected>2 Showers (4.0 GPM)</option>
                <option value="6.0">3 Showers (6.0 GPM)</option>
                <option value="8.0">4 Showers (8.0 GPM)</option>
              </select>
            </div>
            <div>
              <label for="faucetSelect" class="block text-xs font-medium text-slate-400 mb-1">Extra Sinks / Appliances</label>
              <select id="faucetSelect" class="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-rose-500">
                <option value="0.0">None (0.0 GPM)</option>
                <option value="1.5" selected>1 Kitchen Faucet (+1.5 GPM)</option>
                <option value="3.0">Faucet + Dishwasher (+3.0 GPM)</option>
                <option value="4.5">Faucet + Clothes Washer (+4.5 GPM)</option>
              </select>
            </div>
          </div>
        </div>

        <div class="grid grid-cols-2 gap-4">
          <div class="bg-slate-950 border border-rose-500/30 rounded-xl p-4">
            <span class="text-xs uppercase text-rose-400 font-bold">Unit Max Output</span>
            <div class="text-2xl sm:text-3xl font-black text-white mt-1"><span id="unitGpmOut">{gpm_50}</span> <span class="text-sm font-normal text-slate-400">GPM</span></div>
            <p id="deltaNoteOut" class="text-xs text-rose-400 font-semibold mt-1">At +70°F Temp Rise (ΔT)</p>
          </div>

          <div class="bg-slate-950 border border-emerald-500/30 rounded-xl p-4">
            <span class="text-xs uppercase text-emerald-400 font-bold">Your Fixture Demand</span>
            <div class="text-2xl sm:text-3xl font-black text-emerald-400 mt-1"><span id="demandGpmOut">5.5</span> <span class="text-sm font-normal text-slate-400">GPM</span></div>
            <p id="matchStatusOut" class="text-xs text-emerald-400 font-semibold mt-1">✅ Handles Load Easily</p>
          </div>
        </div>
      </div>

      <div class="mt-6 bg-rose-950/40 border border-rose-500/30 rounded-xl p-4 flex flex-col sm:flex-row items-center justify-between gap-4">
        <div id="tanklessAdviceBanner" class="text-sm text-rose-100 font-medium"></div>
        <a id="dynamicHeaterBtn" href="{header_cta_url}" target="_blank" rel="nofollow sponsored" class="shrink-0 bg-rose-500 hover:bg-rose-400 text-white font-extrabold px-4 py-2.5 rounded-lg text-xs uppercase tracking-wider transition">
          Shop Matched Tankless Heater on Amazon →
        </a>
      </div>
    </section>

    <!-- 4-CARD HARDWARE BUNDLE -->
    <section class="mb-12">
      <div class="flex items-center justify-between mb-4">
        <h2 class="text-2xl font-extrabold text-white">Complete {heater_name} Valve, Flush & Anti-Scale Kit</h2>
        <span class="text-xs text-slate-400">CSA, AHRI & Lead-Free Brass Compliant</span>
      </div>
      <div class="grid sm:grid-cols-2 lg:grid-cols-4 gap-4">{bundle_html}</div>
    </section>

    <!-- GROUNDWATER TEMPERATURE & GPM MATRIX TABLE -->
    <section class="mb-12">
      <h2 class="text-2xl font-extrabold text-white mb-4">{heater_name} Flow Rate by US Climate Zone (120°F Hot Water)</h2>
      <div class="overflow-x-auto bg-slate-900 border border-slate-800 rounded-xl">
        <table class="w-full text-left border-collapse text-sm">
          <thead>
            <tr class="border-b border-slate-800 bg-slate-950/60 text-slate-400 uppercase text-xs">
              <th class="py-3.5 px-4">Climate / Groundwater Temp</th>
              <th class="py-3.5 px-4 text-rose-400">Required Temp Rise (ΔT)</th>
              <th class="py-3.5 px-4 text-emerald-400">Continuous Hot Flow (GPM)</th>
              <th class="py-3.5 px-4">Simultaneous Showers</th>
            </tr>
          </thead>
          <tbody>{matrix_rows_html}</tbody>
        </table>
      </div>
    </section>

    <!-- PLUMBING CHECKLIST -->
    <section class="mb-12">
      <div class="flex items-center justify-between mb-4">
        <h2 class="text-2xl font-extrabold text-white">Master Plumber Tankless Installation & Descaling Checklist</h2>
        <span id="tankBadge" class="text-xs font-bold bg-slate-800 text-rose-400 px-3 py-1 rounded-full">0 / 4 Completed</span>
      </div>
      <div class="space-y-3">{checklist_html}</div>
    </section>

    <!-- FAQ -->
    <section class="mb-12">
      <h2 class="text-2xl font-extrabold text-white mb-5">Frequently Asked Questions ({heater_name})</h2>
      <div class="space-y-4">{faqs_html}</div>
    </section>
  </main>

  <footer class="border-t border-slate-800 py-8 text-center text-xs text-slate-500 px-4">
    <p>© {datetime.now(timezone.utc).year} TanklessGPMIndex. Independent Hydronic & Tankless Water Heater Sizing Database. As an Amazon Associate, we earn from qualifying purchases.</p>
  </footer>

  <script>
    const unitEffBtu = {eff_btu_total};
    const amzDomain = "{amz_domain}";
    const amzTag = "{amz_tag}";

    const inletSlider = document.getElementById('inletSlider');
    const targetSlider = document.getElementById('targetSlider');
    const showerSelect = document.getElementById('showerSelect');
    const faucetSelect = document.getElementById('faucetSelect');
    const inletVal = document.getElementById('inletVal');
    const targetVal = document.getElementById('targetVal');
    const unitGpmOut = document.getElementById('unitGpmOut');
    const deltaNoteOut = document.getElementById('deltaNoteOut');
    const demandGpmOut = document.getElementById('demandGpmOut');
    const matchStatusOut = document.getElementById('matchStatusOut');
    const tanklessAdviceBanner = document.getElementById('tanklessAdviceBanner');
    const dynamicHeaterBtn = document.getElementById('dynamicHeaterBtn');

    function recalculateTankless() {{
      const inletF = parseInt(inletSlider.value, 10);
      const targetF = parseInt(targetSlider.value, 10);
      const showerGpm = parseFloat(showerSelect.value);
      const faucetGpm = parseFloat(faucetSelect.value);

      inletVal.textContent = inletF;
      targetVal.textContent = targetF;

      const deltaT = Math.max(20, targetF - inletF);
      const maxGpmAtDelta = unitEffBtu / (500.0 * deltaT);
      const totalDemandGpm = showerGpm + faucetGpm;

      unitGpmOut.textContent = maxGpmAtDelta.toFixed(1);
      deltaNoteOut.textContent = `At +${{deltaT}}°F Temp Rise (ΔT)`;
      demandGpmOut.textContent = totalDemandGpm.toFixed(1);

      const reqBtuForDemand = Math.round((totalDemandGpm * 500.0 * deltaT) / 0.95);
      const reqKwForDemand = Math.round((totalDemandGpm * 500.0 * deltaT) / 3412.0);

      if (totalDemandGpm <= maxGpmAtDelta) {{
        matchStatusOut.textContent = `✅ Plenty (+${{(maxGpmAtDelta - totalDemandGpm).toFixed(1)}} GPM Reserve)`;
        matchStatusOut.className = "text-xs text-emerald-400 font-semibold mt-1";
      }} else {{
        matchStatusOut.textContent = `⚠️ Short by ${{(totalDemandGpm - maxGpmAtDelta).toFixed(1)}} GPM at +${{deltaT}}°F`;
        matchStatusOut.className = "text-xs text-amber-400 font-bold mt-1";
      }}

      let recTier = "199,000 BTU Condensing Gas Tankless";
      let searchQ = "199000+BTU+Condensing+Tankless+Water+Heater+Rinnai+Navien";
      if (reqBtuForDemand <= 120000) {{
        recTier = `140,000 BTU Gas or ${{Math.max(18, reqKwForDemand)}}kW Electric Tankless`;
        searchQ = "150000+BTU+Tankless+Water+Heater+27kW+Electric";
      }} else if (reqBtuForDemand <= 199900) {{
        recTier = "199,000 BTU Super-High-Efficiency Condensing Tankless";
        searchQ = "199000+BTU+Condensing+Tankless+Water+Heater+Rinnai+Navien";
      }} else {{
        recTier = "Dual-Unit Cascade 199,000 BTU Tankless Setup";
        searchQ = "Navien+NPE-240A2+Rinnai+RU199iN+199000+BTU+Tankless";
      }}

      tanklessAdviceBanner.innerHTML = `🔥 <strong>Thermal Sizing Spec:</strong> Supplying <strong>${{totalDemandGpm.toFixed(1)}} GPM at a +${{deltaT}}°F rise</strong> requires <strong>${{reqBtuForDemand.toLocaleString()}} BTU/hr</strong>. Install a <strong>${{recTier}}</strong> with a 3/4" brass service valve kit.`;
      dynamicHeaterBtn.href = `https://${{amzDomain}}/s?k=${{searchQ}}&tag=${{amzTag}}`;
    }}

    inletSlider.addEventListener('input', recalculateTankless);
    targetSlider.addEventListener('input', recalculateTankless);
    showerSelect.addEventListener('change', recalculateTankless);
    faucetSelect.addEventListener('change', recalculateTankless);
    recalculateTankless();

    const checks = document.querySelectorAll('.tank-check');
    const badge = document.getElementById('tankBadge');
    checks.forEach(ch => {{
      ch.addEventListener('change', () => {{
        const done = Array.from(checks).filter(c => c.checked).length;
        badge.textContent = `${{done}} / ${{checks.length}} Completed`;
      }});
    }});
  </script>
</body>
</html>"""

    os.makedirs(DOCS_DIR, exist_ok=True)
    with open(os.path.join(DOCS_DIR, f"{slug}.html"), "w", encoding="utf-8") as f:
        f.write(html)


def rebuild_portal_sitemap_and_rss(published, mon_cfg):
    header_cta = mon_cfg.get("header_cta", {})
    header_cta_url = build_amazon_url(header_cta.get("search_query", "Tankless+Water+Heater+199000+BTU"), mon_cfg)

    cards_html = ""
    for item in reversed(published):
        cards_html += f"""
        <a href="{item['slug']}.html" class="block bg-slate-900 border border-slate-800 hover:border-rose-500/60 rounded-xl p-5 transition group">
          <div class="flex items-center justify-between mb-2">
            <span class="text-xs font-black uppercase bg-rose-500 text-white px-2.5 py-0.5 rounded">{item.get('power_label', '199K BTU')}</span>
            <span class="text-xs text-slate-400">50°F ΔT: {item.get('gpm_50', 7.6)} GPM</span>
          </div>
          <h2 class="text-base font-bold text-white group-hover:text-rose-400 transition">{item['heater_name']} GPM Calculator</h2>
          <p class="text-xs text-slate-400 mt-2 line-clamp-2">{item['description']}</p>
          <span class="inline-block mt-4 text-xs font-extrabold text-rose-400">Calculate ΔT Flow & Showers →</span>
        </a>"""

    index_html = f"""<!DOCTYPE html>
<html lang="en" class="dark">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>TanklessGPMIndex — Tankless Water Heater GPM, Temp Rise (ΔT) & Sizing Calculator (2026)</title>
  <meta name="description" content="Calculate exact tankless water heater GPM flow rate by groundwater temperature rise (ΔT), simultaneous showers, gas BTU, and 240V breaker sizes for Rinnai, Navien, EcoSmart, Stiebel Eltron, and Rheem units.">
  <link rel="canonical" href="{SITE_BASE_URL}/">
  <link rel="alternate" type="application/rss+xml" title="TanklessGPMIndex RSS Feed" href="{SITE_BASE_URL}/rss.xml">
  <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-slate-950 text-slate-100 min-h-screen flex flex-col">
  <header class="border-b border-slate-800 bg-slate-900/80 sticky top-0 z-30 backdrop-blur">
    <div class="max-w-5xl mx-auto px-4 py-3.5 flex items-center justify-between">
      <div class="text-lg font-black text-white flex items-center gap-2">
        <span class="bg-rose-500 text-white px-2 py-0.5 rounded font-black">TANKLESS</span>GPMIndex
      </div>
      <a href="{header_cta_url}" target="_blank" rel="nofollow sponsored" class="text-xs sm:text-sm bg-rose-500 hover:bg-rose-400 text-white font-extrabold px-3.5 py-2 rounded-lg transition">
        {header_cta.get('cta_text', 'Shop Tankless Water Heaters →')}
      </a>
    </div>
  </header>

  <main class="max-w-5xl mx-auto px-4 py-12 flex-1 w-full">
    <div class="text-center max-w-2xl mx-auto mb-10">
      <h1 class="text-3xl sm:text-5xl font-black text-white tracking-tight">Tankless Water Heater GPM & Temp Rise (ΔT) Database</h1>
      <p class="text-slate-400 mt-3 text-base sm:text-lg">Select your tankless water heater model or home bathroom size below to calculate real-world winter vs. summer GPM output, simultaneous showers, and required gas/breaker specs.</p>
      <div class="mt-6">
        <input id="filterInput" type="text" placeholder="Search heater model or home size (e.g. Rinnai RU199iN, Navien NPE-240A2, EcoSmart 27, Stiebel Tempra, 3 Bathroom...)" class="w-full bg-slate-900 border border-slate-700 rounded-xl px-4 py-3.5 text-sm text-white focus:outline-none focus:border-rose-500">
      </div>
    </div>

    <div id="heaterGrid" class="grid sm:grid-cols-2 lg:grid-cols-3 gap-5">{cards_html}</div>
  </main>

  <footer class="border-t border-slate-800 py-8 text-center text-xs text-slate-500">
    <p>© {datetime.now(timezone.utc).year} TanklessGPMIndex. As an Amazon Associate, we earn from qualifying purchases.</p>
  </footer>

  <script>
    const filterInput = document.getElementById('filterInput');
    const cards = Array.from(document.getElementById('heaterGrid').children);
    filterInput.addEventListener('input', (e) => {{
      const q = e.target.value.toLowerCase();
      cards.forEach(c => {{
        c.style.display = c.textContent.toLowerCase().includes(q) ? 'block' : 'none';
      }});
    }});
  </script>
</body>
</html>"""

    os.makedirs(DOCS_DIR, exist_ok=True)
    with open(os.path.join(DOCS_DIR, "index.html"), "w", encoding="utf-8") as f:
        f.write(index_html)

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    urls_xml = f"""  <url>
    <loc>{SITE_BASE_URL}/</loc>
    <lastmod>{today}</lastmod>
    <changefreq>daily</changefreq>
    <priority>1.0</priority>
  </url>\n"""

    for item in published:
        urls_xml += f"""  <url>
    <loc>{SITE_BASE_URL}/{item['slug']}.html</loc>
    <lastmod>{item.get('date', today)}</lastmod>
    <changefreq>monthly</changefreq>
    <priority>0.9</priority>
  </url>\n"""

    with open(os.path.join(DOCS_DIR, "sitemap.xml"), "w", encoding="utf-8") as f:
        f.write(f"""<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n{urls_xml}</urlset>""")

    rss_items = ""
    for item in list(reversed(published))[:30]:
        rss_items += f"""    <item>
      <title>{item['title']}</title>
      <link>{SITE_BASE_URL}/{item['slug']}.html</link>
      <guid>{SITE_BASE_URL}/{item['slug']}.html</guid>
      <description>{item['description']}</description>
    </item>\n"""

    rss_xml = f"""<?xml version="1.0" encoding="UTF-8" ?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">
  <channel>
    <title>TanklessGPMIndex On-Demand Water Heater Sizing Database</title>
    <link>{SITE_BASE_URL}/</link>
    <description>Interactive Tankless Water Heater GPM Flow Rate, Delta-T & Breaker Calculators</description>
    <atom:link href="{SITE_BASE_URL}/rss.xml" rel="self" type="application/rss+xml" />
    <atom:link href="https://pubsubhubbub.appspot.com/" rel="hub" />
{rss_items}  </channel>
</rss>"""

    with open(os.path.join(DOCS_DIR, "rss.xml"), "w", encoding="utf-8") as f:
        f.write(rss_xml)

    with open(os.path.join(DOCS_DIR, "robots.txt"), "w", encoding="utf-8") as f:
        f.write(f"User-agent: *\nAllow: /\nSitemap: {SITE_BASE_URL}/sitemap.xml\n")

    with open(os.path.join(DOCS_DIR, f"{INDEXNOW_KEY}.txt"), "w", encoding="utf-8") as f:
        f.write(INDEXNOW_KEY)


def notify_search_engines(new_urls):
    if not SITE_BASE_URL or not new_urls:
        return
    parsed_host = urllib.parse.urlparse(SITE_BASE_URL).netloc
    payload = {
        "host": parsed_host,
        "key": INDEXNOW_KEY,
        "keyLocation": f"{SITE_BASE_URL}/{INDEXNOW_KEY}.txt",
        "urlList": new_urls
    }
    try:
        req = urllib.request.Request(
            "https://api.indexnow.org/indexnow",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json; charset=utf-8"},
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            print(f"[INDEXNOW] Pushed {len(new_urls)} URLs (HTTP {resp.status})")
    except Exception as e:
        print(f"[WARN] IndexNow ping notice: {e}")

    try:
        hub_data = urllib.parse.urlencode({
            "hub.mode": "publish",
            "hub.url": f"{SITE_BASE_URL}/rss.xml"
        }).encode("utf-8")
        req_hub = urllib.request.Request(
            "https://pubsubhubbub.appspot.com/",
            data=hub_data,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            method="POST"
        )
        with urllib.request.urlopen(req_hub, timeout=15) as resp_hub:
            print(f"[WEBSUB] Google PubSubHubbub ping status: {resp_hub.status}")
    except Exception as e:
        print(f"[WARN] WebSub ping notice: {e}")


def main():
    published = load_json(PUBLISHED_FILE, [])
    mon_cfg = load_json(MONETIZATION_FILE, {})
    published_slugs = {item["slug"] for item in published}

    candidates = []
    if CUSTOM_HEATER:
        candidates.append((CUSTOM_HEATER.strip(), "Natural Gas / LP", 199000, 0.96, "3/4\" Gas Line + 2\" PVC Vent", 10.5))
    candidates.extend(SEED_HEATERS)
    candidates.extend(discover_google_tankless_queries())

    new_urls = []
    count = 0

    for heater_tuple in candidates:
        if count >= PAGES_PER_RUN:
            break
        h_name = heater_tuple[0]
        slug = slugify(f"{h_name}-gpm-temp-rise-calculator")
        if slug in published_slugs:
            continue

        print(f"[ENGINE] Generating tankless water heater GPM & Delta-T calculator for: {h_name}...")
        try:
            data = generate_tankless_data(heater_tuple)
            build_tankless_html_page(data, slug, mon_cfg)
            today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
            sp = data.get("specs", {})
            p_val = safe_float(sp.get("power_rating", heater_tuple[2]), heater_tuple[2])
            p_lbl = f"{int(p_val)} kW Electric" if p_val <= 100 else f"{int(p_val // 1000)}K BTU Gas"

            published.append({
                "heater_name": data.get("heater_name", h_name),
                "slug": slug,
                "title": data.get("seo_title", f"{h_name} GPM Calculator"),
                "description": data.get("meta_description", ""),
                "power_label": p_lbl,
                "gpm_50": round(safe_float(sp.get("gpm_at_50f_rise", 7.6), 7.6), 1),
                "date": today
            })
            published_slugs.add(slug)
            if SITE_BASE_URL:
                new_urls.append(f"{SITE_BASE_URL}/{slug}.html")
            count += 1
            time.sleep(2)
        except Exception as e:
            print(f"[ERROR] Failed building {h_name}: {e}")

    save_json(PUBLISHED_FILE, published)
    rebuild_portal_sitemap_and_rss(published, mon_cfg)
    if new_urls and SITE_BASE_URL:
        new_urls.append(f"{SITE_BASE_URL}/")
        notify_search_engines(new_urls)
    print(f"[DONE] Published {count} new tankless water heater GPM calculator pages.")


if __name__ == "__main__":
    main()
