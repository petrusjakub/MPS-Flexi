"""
Convert Data_Premi_MPS_Clean_FULL.csv to dataPremiJSON format for MPS_Flexi_Updated.html.

Only uses the 100_Ribu column (index 6):
- For IDR: value * 1,000,000 = annual kontribusi in Rupiah for UP 1 Miliar
- For USD: value as integer = annual kontribusi in USD for UP USD 100,000
- "-" means no data (skip)

Output: JSON array entries like:
  {"plan":"A","gender":"pria","curr":"IDR","age":40,"mb":1,"ml":1,"rate":4100000}
"""

import re
import json

PLAN_MAP = {
    "Flexi Amanah": "A",
    "Flexi Berkah": "B",
    "Flexi Cermat": "C",
}


def parse_csv_line(line):
    """Parse a CSV line handling commas as thousands separators in numbers."""
    parts = line.strip().split(',')
    if len(parts) == 16:
        return parts
    first6 = parts[:6]
    rest = parts[6:]
    values = []
    i = 0
    while i < len(rest):
        current = rest[i]
        while (i + 1 < len(rest) and
               re.match(r'^(\d{1,3},)*\d{1,3}$', current) and
               re.match(r'^\d{3}(\.\d+)?$', rest[i+1])):
            i += 1
            current += ',' + rest[i]
        values.append(current)
        i += 1
    return first6 + values


def parse_rate(value_str, currency):
    """Convert rate string to integer.
    For IDR: multiply by 1,000,000
    For USD: use as-is (integer)
    Returns None if value is '-' or invalid.
    """
    value_str = value_str.strip()
    if value_str == '-' or value_str == '':
        return None
    # Remove thousands separator commas
    clean = value_str.replace(',', '')
    try:
        num = float(clean)
    except ValueError:
        return None
    if currency == 'IDR':
        return round(num * 1_000_000)
    else:  # USD
        return int(round(num))


def main():
    with open('Data_Premi_MPS_Clean_FULL.csv', 'r') as f:
        lines = f.readlines()

    # Skip header
    data_lines = lines[1:]

    entries = []
    # Track current term for Plan C grouping
    current_cermat_term = None

    for line in data_lines:
        row = parse_csv_line(line)
        if len(row) != 16:
            continue

        currency = row[0].strip()  # IDR or USD
        age = int(row[1].strip())
        gender_raw = row[2].strip()  # PRIA or WANITA
        plan_raw = row[3].strip()  # Flexi Amanah, Flexi Berkah, Flexi Cermat
        term = row[4].strip()  # YRT, 5, 10, 15, 25, 35, 110, 70, 65, etc. or empty
        ppp = row[5].strip()  # 1, 5, 10, 15
        rate_str = row[6]  # 100_Ribu column

        # Map values
        plan = PLAN_MAP.get(plan_raw)
        if plan is None:
            continue

        gender = gender_raw.lower()  # pria or wanita
        curr = currency.upper()

        # Parse rate
        rate = parse_rate(rate_str, curr)
        if rate is None:
            continue

        mb = int(ppp)

        # Determine ml based on plan
        if plan == 'A':
            # Plan A: PPP=1,Term=YRT -> mb=1,ml=1; PPP=5,Term=5 -> mb=5,ml=5; PPP=10,Term=10 -> mb=10,ml=10
            if mb == 1:
                ml = 1
            elif mb == 5:
                ml = 5
            elif mb == 10:
                ml = 10
            else:
                continue
        elif plan == 'B':
            # Plan B: ml is ALWAYS 110
            ml = 110
        elif plan == 'C':
            # Plan C: Term column has value on first row of each term group
            if term:
                current_cermat_term = int(term)
            ml = current_cermat_term
            if ml is None:
                continue
        else:
            continue

        entry = {
            "plan": plan,
            "gender": gender,
            "curr": curr,
            "age": age,
            "mb": mb,
            "ml": ml,
            "rate": rate,
        }
        entries.append(entry)

    print(f"Total entries generated: {len(entries)}")

    # Write JSON output
    with open('dataPremiJSON_output.json', 'w') as f:
        json.dump(entries, f, separators=(',', ':'))

    # Also write formatted for inspection
    with open('dataPremiJSON_output_formatted.json', 'w') as f:
        json.dump(entries[:20], f, indent=2)

    print(f"Output written to dataPremiJSON_output.json")
    print(f"Sample (first 5):")
    for e in entries[:5]:
        print(f"  {json.dumps(e, separators=(',', ':'))}")


if __name__ == '__main__':
    main()
