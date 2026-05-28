"""
Extract premium data from Data_Premi_MPS_Clean.json and output dataPremiJSON entries
for MPS_Flexi_Updated.html.

Each 17-row block:
  Offset 0: Amanah header
  Offset 1: Amanah MB=1 (YRT), PPP=1
  Offset 2: Amanah MB=5, PPP=5
  Offset 3: Amanah MB=10, PPP=10
  Offset 4: Berkah header
  Offset 5: Berkah MB=5, PPP=5
  Offset 6: Berkah MB=10, PPP=10 (col 1 = Berkah Term)
  Offset 7: Berkah MB=15, PPP=15
  Offset 8: Cermat header
  Offset 9: Cermat Term15/MB=5
  Offset 10: Cermat Term15/MB=10 (col 1 has "15")
  Offset 11: Cermat Term25/MB=5
  Offset 12: Cermat Term25/MB=10 (col 1 has "25")
  Offset 13: Cermat Term25/MB=15
  Offset 14: Cermat Term35/MB=5
  Offset 15: Cermat Term35/MB=10 (col 1 has "35")
  Offset 16: Cermat Term35/MB=15
"""

import json

with open('Data_Premi_MPS_Clean.json') as f:
    data = json.load(f)


def parse_value(val_str, is_usd):
    """Parse a value string to an integer rate.
    IDR values are in Juta (millions) -> multiply by 1,000,000.
    USD values are already in USD (with comma thousands separator).
    Returns None if value is '-' or empty.
    """
    if not val_str or val_str.strip() == '' or val_str.strip() == '-':
        return None
    val_str = val_str.strip()
    if is_usd:
        # Remove commas: "7,258" -> "7258"
        val_str = val_str.replace(',', '')
        return int(round(float(val_str)))
    else:
        # IDR: "17.2" means 17.2 Juta -> 17,200,000
        val_str = val_str.replace(',', '')
        return int(round(float(val_str) * 1_000_000))


# Parse all blocks
blocks = []
i = 76
while i + 16 < len(data):
    row = data[i]
    if row[0] == 'Plan':
        is_usd = 'Ribu' in str(row[3])
        berkah_row = data[i + 6]
        berkah_term = berkah_row[1]
        age = 110 - int(berkah_term) if berkah_term else None
        blocks.append({
            'start_row': i,
            'is_usd': is_usd,
            'age': age,
        })
        i += 17
    else:
        i += 1

# Assign gender based on block order within each age group
# Normal pattern (4 blocks): IDR Pria, USD Pria, IDR Wanita, USD Wanita
# Special cases:
#   Age 7: 3 blocks [IDR, IDR, USD] = IDR Pria, IDR Wanita, USD Wanita
#   Age 15: 3 blocks [IDR, USD, USD] = IDR Pria, USD Pria, USD Wanita
#   Age 39: 1 block [USD] = USD Pria
#   Ages 65-70: 2 blocks [USD, USD] = USD Pria, USD Wanita

from collections import defaultdict
age_blocks = defaultdict(list)
for b in blocks:
    age_blocks[b['age']].append(b)

for age, blks in age_blocks.items():
    n = len(blks)
    currencies = [b['is_usd'] for b in blks]

    if n == 4:
        # Standard: IDR Pria, USD Pria, IDR Wanita, USD Wanita
        blks[0]['gender'] = 'pria'
        blks[1]['gender'] = 'pria'
        blks[2]['gender'] = 'wanita'
        blks[3]['gender'] = 'wanita'
    elif n == 3 and currencies == [False, False, True]:
        # Age 7: IDR Pria, IDR Wanita, USD Wanita
        blks[0]['gender'] = 'pria'
        blks[1]['gender'] = 'wanita'
        blks[2]['gender'] = 'wanita'
    elif n == 3 and currencies == [False, True, True]:
        # Age 15: IDR Pria, USD Pria, USD Wanita
        blks[0]['gender'] = 'pria'
        blks[1]['gender'] = 'pria'
        blks[2]['gender'] = 'wanita'
    elif n == 2 and currencies == [True, True]:
        # Ages 65-70: USD Pria, USD Wanita
        blks[0]['gender'] = 'pria'
        blks[1]['gender'] = 'wanita'
    elif n == 1 and currencies == [True]:
        # Age 39: USD Pria
        blks[0]['gender'] = 'pria'
    else:
        raise ValueError(f"Unexpected pattern for age {age}: {n} blocks, currencies={currencies}")

# Now extract all entries
entries = []

for b in blocks:
    start = b['start_row']
    is_usd = b['is_usd']
    age = b['age']
    gender = b['gender']
    curr = 'USD' if is_usd else 'IDR'

    # Column 3 = first UP level rate (UP 1 Miliar for IDR, UP 100K for USD)
    col = 3  # We only need col 3 as per the task spec

    # Plan A (Amanah): offsets 1, 2, 3
    # Offset 1: mb=1, ml=1 (YRT)
    val = parse_value(data[start + 1][col], is_usd)
    if val is not None:
        entries.append({"plan": "A", "gender": gender, "curr": curr, "age": age, "mb": 1, "ml": 1, "rate": val})

    # Offset 2: mb=5, ml=5
    val = parse_value(data[start + 2][col], is_usd)
    if val is not None:
        entries.append({"plan": "A", "gender": gender, "curr": curr, "age": age, "mb": 5, "ml": 5, "rate": val})

    # Offset 3: mb=10, ml=10
    val = parse_value(data[start + 3][col], is_usd)
    if val is not None:
        entries.append({"plan": "A", "gender": gender, "curr": curr, "age": age, "mb": 10, "ml": 10, "rate": val})

    # Plan B (Berkah): offsets 5, 6, 7 - always ml=110
    # Offset 5: mb=5, ml=110
    val = parse_value(data[start + 5][col], is_usd)
    if val is not None:
        entries.append({"plan": "B", "gender": gender, "curr": curr, "age": age, "mb": 5, "ml": 110, "rate": val})

    # Offset 6: mb=10, ml=110
    val = parse_value(data[start + 6][col], is_usd)
    if val is not None:
        entries.append({"plan": "B", "gender": gender, "curr": curr, "age": age, "mb": 10, "ml": 110, "rate": val})

    # Offset 7: mb=15, ml=110
    val = parse_value(data[start + 7][col], is_usd)
    if val is not None:
        entries.append({"plan": "B", "gender": gender, "curr": curr, "age": age, "mb": 15, "ml": 110, "rate": val})

    # Plan C (Cermat): offsets 9-16
    # Offset 9: Term15/MB=5 -> mb=5, ml=15
    val = parse_value(data[start + 9][col], is_usd)
    if val is not None:
        entries.append({"plan": "C", "gender": gender, "curr": curr, "age": age, "mb": 5, "ml": 15, "rate": val})

    # Offset 10: Term15/MB=10 -> mb=10, ml=15
    val = parse_value(data[start + 10][col], is_usd)
    if val is not None:
        entries.append({"plan": "C", "gender": gender, "curr": curr, "age": age, "mb": 10, "ml": 15, "rate": val})

    # Offset 11: Term25/MB=5 -> mb=5, ml=25
    val = parse_value(data[start + 11][col], is_usd)
    if val is not None:
        entries.append({"plan": "C", "gender": gender, "curr": curr, "age": age, "mb": 5, "ml": 25, "rate": val})

    # Offset 12: Term25/MB=10 -> mb=10, ml=25
    val = parse_value(data[start + 12][col], is_usd)
    if val is not None:
        entries.append({"plan": "C", "gender": gender, "curr": curr, "age": age, "mb": 10, "ml": 25, "rate": val})

    # Offset 13: Term25/MB=15 -> mb=15, ml=25
    val = parse_value(data[start + 13][col], is_usd)
    if val is not None:
        entries.append({"plan": "C", "gender": gender, "curr": curr, "age": age, "mb": 15, "ml": 25, "rate": val})

    # Offset 14: Term35/MB=5 -> mb=5, ml=35
    val = parse_value(data[start + 14][col], is_usd)
    if val is not None:
        entries.append({"plan": "C", "gender": gender, "curr": curr, "age": age, "mb": 5, "ml": 35, "rate": val})

    # Offset 15: Term35/MB=10 -> mb=10, ml=35
    val = parse_value(data[start + 15][col], is_usd)
    if val is not None:
        entries.append({"plan": "C", "gender": gender, "curr": curr, "age": age, "mb": 10, "ml": 35, "rate": val})

    # Offset 16: Term35/MB=15 -> mb=15, ml=35
    val = parse_value(data[start + 16][col], is_usd)
    if val is not None:
        entries.append({"plan": "C", "gender": gender, "curr": curr, "age": age, "mb": 15, "ml": 35, "rate": val})

# Output as JSON array
print(json.dumps(entries, separators=(',', ':')))
