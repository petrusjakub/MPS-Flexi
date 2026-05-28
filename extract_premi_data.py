#!/usr/bin/env python3
"""
Extract premium data from Data_Premi_MPS_Clean.json and populate
MPS_Flexi_Updated.html with a complete data-driven lookup.
"""

import json
import re
from collections import defaultdict


def parse_rate(value, currency):
    """Parse a rate value based on currency type."""
    value = value.strip()
    if value == '-' or value == '':
        return None
    if currency == 'IDR':
        # Value is in Juta (millions), e.g. "17.2" -> 17200000
        return int(float(value) * 1_000_000)
    else:
        # USD: remove commas, parse as int, e.g. "7,258" -> 7258
        return int(value.replace(',', ''))


def extract_block(block_rows, age, gender, currency):
    """Extract all premium entries from a 17-row block."""
    entries = []

    # Plan A (Amanah): offsets 1, 2, 3
    plan_a_map = [
        (1, 1, 1),    # offset 1: mb=1, ml=1 (YRT)
        (2, 5, 5),    # offset 2: mb=5, ml=5
        (3, 10, 10),  # offset 3: mb=10, ml=10
    ]
    for offset, mb, ml in plan_a_map:
        rate = parse_rate(block_rows[offset][3], currency)
        if rate is not None:
            entries.append({
                "plan": "A",
                "gender": gender,
                "curr": currency,
                "age": age,
                "mb": mb,
                "ml": ml,
                "rate": rate
            })

    # Plan B (Berkah): offsets 5, 6, 7
    plan_b_map = [
        (5, 5, 110),   # offset 5: mb=5, ml=110
        (6, 10, 110),  # offset 6: mb=10, ml=110
        (7, 15, 110),  # offset 7: mb=15, ml=110
    ]
    for offset, mb, ml in plan_b_map:
        rate = parse_rate(block_rows[offset][3], currency)
        if rate is not None:
            entries.append({
                "plan": "B",
                "gender": gender,
                "curr": currency,
                "age": age,
                "mb": mb,
                "ml": ml,
                "rate": rate
            })

    # Plan C (Cermat): offsets 9-16
    plan_c_map = [
        (9, 5, 15),    # Term15, mb=5
        (10, 10, 15),  # Term15, mb=10
        (11, 5, 25),   # Term25, mb=5
        (12, 10, 25),  # Term25, mb=10
        (13, 15, 25),  # Term25, mb=15
        (14, 5, 35),   # Term35, mb=5
        (15, 10, 35),  # Term35, mb=10
        (16, 15, 35),  # Term35, mb=15
    ]
    for offset, mb, ml in plan_c_map:
        rate = parse_rate(block_rows[offset][3], currency)
        if rate is not None:
            entries.append({
                "plan": "C",
                "gender": gender,
                "curr": currency,
                "age": age,
                "mb": mb,
                "ml": ml,
                "rate": rate
            })

    return entries


def main():
    # Load JSON data
    with open('/projects/sandbox/MPS-Flexi/Data_Premi_MPS_Clean.json', 'r') as f:
        data = json.load(f)

    # Skip rows 0-75, process rows 76-2370 as 135 blocks of 17 rows
    blocks_data = []
    for i in range(135):
        start = 76 + i * 17
        block_rows = data[start:start + 17]

        # Detect currency from header row (offset 0), col index 3
        header_col3 = block_rows[0][3]
        if header_col3 == '1M':
            currency = 'IDR'
        elif 'Ribu' in header_col3:
            currency = 'USD'
        else:
            currency = 'IDR'  # fallback

        # Detect age from Berkah offset 6, col index 1 (term number)
        term_val = block_rows[6][1].strip()
        age = 110 - int(term_val)

        blocks_data.append({
            'index': i,
            'age': age,
            'currency': currency,
            'rows': block_rows
        })

    # Group blocks by age
    age_groups = defaultdict(list)
    for block in blocks_data:
        age_groups[block['age']].append(block)

    # Assign gender based on position within age group
    all_entries = []
    for age in sorted(age_groups.keys()):
        group = age_groups[age]
        n = len(group)
        currs = [b['currency'] for b in group]

        if n == 4:
            # Normal: [IDR_Pria, USD_Pria, IDR_Wanita, USD_Wanita]
            genders = ['pria', 'pria', 'wanita', 'wanita']
        elif n == 3:
            # Special cases
            if currs == ['IDR', 'IDR', 'USD']:
                # Age 7: IDR Pria, IDR Wanita, USD Wanita
                genders = ['pria', 'wanita', 'wanita']
            elif currs == ['IDR', 'USD', 'USD']:
                # Age 15: IDR Pria, USD Pria, USD Wanita
                genders = ['pria', 'pria', 'wanita']
            else:
                # Fallback: first half pria, rest wanita
                genders = ['pria', 'pria', 'wanita']
        elif n == 2:
            # Ages 65-70 (both USD): [Pria, Wanita]
            genders = ['pria', 'wanita']
        elif n == 1:
            # Age 39 (single USD block): Pria
            genders = ['pria']
        else:
            genders = ['pria'] * n

        for block, gender in zip(group, genders):
            entries = extract_block(block['rows'], age, gender, block['currency'])
            all_entries.extend(entries)

    print(f"Total entries extracted: {len(all_entries)}")

    # Verify data diversity
    ages = set(e['age'] for e in all_entries)
    plans = set(e['plan'] for e in all_entries)
    currs = set(e['curr'] for e in all_entries)
    genders = set(e['gender'] for e in all_entries)
    print(f"Ages: {sorted(ages)}")
    print(f"Plans: {plans}")
    print(f"Currencies: {currs}")
    print(f"Genders: {genders}")

    # Format as JavaScript array
    js_entries = json.dumps(all_entries, separators=(',', ':'))

    # Build the replacement code
    new_code = f"""// Data Premi MPS Flexi - Extracted from Data_Premi_MPS_Clean.json
const dataPremiJSON = {js_entries};

function getBaseRate(plan, gender, age, mb, ml) {{
    const currency = document.getElementById('calc-currency').value;
    const entry = dataPremiJSON.find(d => d.plan === plan && d.gender === gender && d.age === age && d.mb === mb && d.ml === ml && d.curr === currency);
    return entry ? entry.rate : null;
}}"""

    # Read the HTML file
    with open('/projects/sandbox/MPS-Flexi/MPS_Flexi_Updated.html', 'r', encoding='utf-8') as f:
        html = f.read()

    # Replace the getBaseRate section
    # Pattern: from "// Database Mockup" comment through closing brace of getBaseRate
    pattern = r'// Database Mockup Spesifik.*?return 10000000; // Dummy Base Rate\n\}'
    match = re.search(pattern, html, re.DOTALL)
    if not match:
        print("ERROR: Could not find getBaseRate section to replace!")
        return

    html = html[:match.start()] + new_code + html[match.end():]
    print("Replaced getBaseRate section successfully.")

    # Add null check in calculate() function after ratePerMiliar assignment
    null_check = """    let ratePerMiliar = getBaseRate(plan, gender, age, mb, ml);

    if (ratePerMiliar === null) {
        document.getElementById('result-label').innerText = '';
        document.getElementById('calc-premium').innerHTML = '<span style=\"color:#e53935\">DATA BELUM ADA</span>';
        document.getElementById('calc-detail').innerHTML = 'Data premi untuk kombinasi ini belum tersedia dalam database.';
        document.getElementById('calc-note').innerHTML = '';
        return;
    }"""

    old_rate_line = "    let ratePerMiliar = getBaseRate(plan, gender, age, mb, ml);"
    if old_rate_line in html:
        html = html.replace(old_rate_line, null_check, 1)
        print("Added null check for ratePerMiliar.")
    else:
        print("WARNING: Could not find ratePerMiliar line to add null check!")

    # Write the updated HTML back
    with open('/projects/sandbox/MPS-Flexi/MPS_Flexi_Updated.html', 'w', encoding='utf-8') as f:
        f.write(html)

    print("HTML file updated successfully.")


if __name__ == '__main__':
    main()
