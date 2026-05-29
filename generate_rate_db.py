#!/usr/bin/env python3
"""
Generate rate database JSON from Data_Premi_MPS_Clean_FULL.csv.
Handles thousand-separator commas in numeric fields.
Output format: JSON object with keys "CURRENCY|PLAN_SHORT|GENDER_SHORT|AGE|MASA_BAYAR|MASA_PERLINDUNGAN"
Values are arrays of 10 numbers (0 for unavailable '-').
"""

import re
import json
import sys
import os


def parse_csv_line(line):
    """
    Custom CSV parser that handles thousand-separator commas.
    The first 6 fields (Mata_Uang, Usia, Gender, Plan, Term, PPP) are always clean.
    Rate fields (positions 6+) may have thousand separators causing extra splits.
    Strategy: Split by comma. If total fields > 16, merge rate fields where current
    field is pure digits (no decimal) and next field matches 3 digits with optional decimal.
    If total fields == 16, no merging needed.
    """
    parts = line.strip().split(',')

    # If we have exactly 16 fields, no thousand separators present
    if len(parts) <= 16:
        return parts

    # First 6 fields are always clean
    clean_fields = parts[:6]

    # Rate fields need merging
    rate_parts = parts[6:]
    merged_rates = []
    i = 0
    while i < len(rate_parts):
        current = rate_parts[i].strip()
        # Check if this is the start of a thousand-separated number:
        # Current is pure digits (no decimal point) AND next field matches 3 digits with optional decimal
        if (i + 1 < len(rate_parts) and
            len(merged_rates) < 10 and
            re.match(r'^\d+$', current) and
            re.match(r'^\d{3}(\.\d+)?$', rate_parts[i + 1].strip())):
            # Merge: concatenate without comma (the comma was the thousand separator)
            merged_rates.append(current + rate_parts[i + 1].strip())
            i += 2
        else:
            merged_rates.append(current)
            i += 1

    return clean_fields + merged_rates


def parse_rate_value(val):
    """Convert a rate string to a float. Returns 0 for '-' or empty."""
    val = val.strip()
    if val == '-' or val == '' or val == '0':
        return 0.0
    try:
        return float(val)
    except ValueError:
        return 0.0


def main():
    csv_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'Data_Premi_MPS_Clean_FULL.csv')

    rate_db = {}
    plan_map = {
        'Flexi Amanah': 'A',
        'Flexi Berkah': 'B',
        'Flexi Cermat': 'C'
    }
    gender_map = {
        'PRIA': 'M',
        'WANITA': 'F'
    }

    # Track current Term for Cermat (empty Term inherits from previous non-empty Term row)
    # We track per (currency, gender, age) group
    current_term_cermat = {}

    with open(csv_path, 'r', encoding='utf-8') as f:
        header = f.readline()  # skip header

        for line in f:
            if not line.strip():
                continue

            fields = parse_csv_line(line)
            if len(fields) < 16:
                # Pad with zeros if somehow short
                fields += ['0'] * (16 - len(fields))

            currency = fields[0].strip()
            age = fields[1].strip()
            gender = fields[2].strip()
            plan_full = fields[3].strip()
            term = fields[4].strip()
            ppp = fields[5].strip()

            plan_short = plan_map.get(plan_full, '')
            gender_short = gender_map.get(gender, '')

            if not plan_short or not gender_short:
                continue

            # Parse the 10 rate values
            rates = []
            for i in range(6, 16):
                rates.append(parse_rate_value(fields[i]))

            # Determine masa_bayar and masa_perlindungan based on plan
            if plan_short == 'A':
                # Amanah: Term = YRT/5/10, PPP = 1/5/10
                # masa_bayar = PPP value, masa_perlindungan = Term value
                masa_bayar = ppp  # "1", "5", or "10"
                masa_perlindungan = term  # "YRT", "5", or "10"
                if not masa_bayar or not masa_perlindungan:
                    continue

            elif plan_short == 'B':
                # Berkah: Masa Perlindungan always = 110
                # PPP = 5/10/15, Term column shows (110-age) for PPP=5, empty for others
                masa_bayar = ppp
                masa_perlindungan = '110'
                if not masa_bayar:
                    continue

            elif plan_short == 'C':
                # Cermat: Term = 15/25/35 (Masa Perlindungan), PPP = 5/10/15
                # Rows with empty Term inherit from previous non-empty Term row
                group_key = (currency, gender, age)
                if term:
                    current_term_cermat[group_key] = term
                    masa_perlindungan = term
                else:
                    masa_perlindungan = current_term_cermat.get(group_key, '')

                masa_bayar = ppp
                if not masa_bayar or not masa_perlindungan:
                    continue
            else:
                continue

            # Build the key
            key = f"{currency}|{plan_short}|{gender_short}|{age}|{masa_bayar}|{masa_perlindungan}"

            # Round rates to 1 decimal place to save space
            rounded_rates = [round(r, 1) for r in rates]
            rate_db[key] = rounded_rates

    # Output as JSON
    json.dump(rate_db, sys.stdout, separators=(',', ':'))


if __name__ == '__main__':
    main()
