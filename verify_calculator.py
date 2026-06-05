#!/usr/bin/env python3
"""
Verification script for the MPS Flexi Calculator.
Extracts the RATE_DB from the HTML and verifies the 3 reference test cases.
"""

import json
import re
import os
import sys

script_dir = os.path.dirname(os.path.abspath(__file__))
html_path = os.path.join(script_dir, 'MPS_Flexi_Updated.html')

def extract_rate_db(html_content):
    """Extract the RATE_DB JSON from the HTML file."""
    # Find the const RATE_DB = {...}; pattern
    match = re.search(r'const RATE_DB = ({.*?});', html_content, re.DOTALL)
    if not match:
        return None
    return json.loads(match.group(1))


def verify_test_cases(db):
    """Verify the 3 reference test cases from PDF filenames."""
    results = []
    tolerance = 0.05  # 5% tolerance

    # Test case 1: Pria 40th Flexi A 1M (1 Miliar) MPP YRT -> Premi ~Rp 4.12Jt/tahun
    key1 = 'IDR|A|M|40|1|YRT'
    rates1 = db.get(key1)
    if rates1:
        # Index 8 = 1_Juta column (1 Miliar UP)
        rate1 = rates1[8]
        premi1 = rate1 * 100000  # IDR multiplier
        expected1 = 4120000
        pct_diff1 = abs(premi1 - expected1) / expected1
        pass1 = pct_diff1 <= tolerance
        results.append({
            'name': 'Pria 40, Amanah YRT, UP 1M IDR',
            'expected': expected1,
            'actual': premi1,
            'pct_diff': pct_diff1,
            'passed': pass1
        })
    else:
        results.append({
            'name': 'Pria 40, Amanah YRT, UP 1M IDR',
            'expected': 4120000,
            'actual': 'KEY NOT FOUND',
            'pct_diff': 1.0,
            'passed': False
        })

    # Test case 2: Pria 40th Flexi B 1M MPP 15th -> Premi ~Rp 20.65Jt/tahun
    key2 = 'IDR|B|M|40|15|110'
    rates2 = db.get(key2)
    if rates2:
        rate2 = rates2[8]
        premi2 = rate2 * 100000
        expected2 = 20650000
        pct_diff2 = abs(premi2 - expected2) / expected2
        pass2 = pct_diff2 <= tolerance
        results.append({
            'name': 'Pria 40, Berkah PPP=15, UP 1M IDR',
            'expected': expected2,
            'actual': premi2,
            'pct_diff': pct_diff2,
            'passed': pass2
        })
    else:
        results.append({
            'name': 'Pria 40, Berkah PPP=15, UP 1M IDR',
            'expected': 20650000,
            'actual': 'KEY NOT FOUND',
            'pct_diff': 1.0,
            'passed': False
        })

    # Test case 3: Pria 40th Flexi C 1M Term 15th MPP 5th -> Premi ~Rp 142.86Jt/tahun
    key3 = 'IDR|C|M|40|5|15'
    rates3 = db.get(key3)
    if rates3:
        rate3 = rates3[8]
        premi3 = rate3 * 100000
        expected3 = 142860000
        pct_diff3 = abs(premi3 - expected3) / expected3
        pass3 = pct_diff3 <= tolerance
        results.append({
            'name': 'Pria 40, Cermat T15 PPP5, UP 1M IDR',
            'expected': expected3,
            'actual': premi3,
            'pct_diff': pct_diff3,
            'passed': pass3
        })
    else:
        results.append({
            'name': 'Pria 40, Cermat T15 PPP5, UP 1M IDR',
            'expected': 142860000,
            'actual': 'KEY NOT FOUND',
            'pct_diff': 1.0,
            'passed': False
        })

    # Test case 4 (bonus): USD Pria 40 Amanah YRT UP 1M USD -> Premi USD 4120
    key4 = 'USD|A|M|40|1|YRT'
    rates4 = db.get(key4)
    if rates4:
        rate4 = rates4[8]  # 1M USD column
        premi4 = rate4 * 1  # USD multiplier is 1
        expected4 = 4120
        pct_diff4 = abs(premi4 - expected4) / expected4
        pass4 = pct_diff4 <= tolerance
        results.append({
            'name': 'Pria 40, Amanah YRT, UP 1M USD',
            'expected': expected4,
            'actual': premi4,
            'pct_diff': pct_diff4,
            'passed': pass4
        })
    else:
        results.append({
            'name': 'Pria 40, Amanah YRT, UP 1M USD',
            'expected': 4120,
            'actual': 'KEY NOT FOUND',
            'pct_diff': 1.0,
            'passed': False
        })

    return results


def verify_password(html_content):
    """Verify the komisi password is '123'."""
    return "pwd === '123'" in html_content


def verify_frequency_multipliers(html_content):
    """Verify frequency multipliers are present in the payment mode select or JS code."""
    has_tahunan = 'Tahunan' in html_content or 'tahunan' in html_content
    has_semesteran = '0.525' in html_content
    has_kuartalan = '0.275' in html_content
    has_bulanan = '0.095' in html_content
    return has_tahunan and has_semesteran and has_kuartalan and has_bulanan


def main():
    print("=" * 60)
    print("MPS Flexi Calculator Verification")
    print("=" * 60)

    with open(html_path, 'r', encoding='utf-8') as f:
        html_content = f.read()

    # Extract RATE_DB
    print("\n1. Extracting RATE_DB from HTML...")
    db = extract_rate_db(html_content)
    if db is None:
        print("   FAIL: Could not extract RATE_DB from HTML")
        sys.exit(1)
    print(f"   OK: Found {len(db)} entries in RATE_DB")

    # Verify entry count
    expected_entries = 3976
    if len(db) == expected_entries:
        print(f"   OK: Entry count matches expected ({expected_entries})")
    else:
        print(f"   WARN: Entry count {len(db)} differs from expected {expected_entries}")

    # Verify test cases
    print("\n2. Verifying reference test cases...")
    results = verify_test_cases(db)
    all_passed = True
    for r in results:
        status = "PASS" if r['passed'] else "FAIL"
        if r['passed']:
            print(f"   {status}: {r['name']}")
            print(f"         Expected: {r['expected']}, Got: {r['actual']} (diff: {r['pct_diff']*100:.2f}%)")
        else:
            print(f"   {status}: {r['name']}")
            print(f"         Expected: {r['expected']}, Got: {r['actual']} (diff: {r['pct_diff']*100:.2f}%)")
            all_passed = False

    # Verify password
    print("\n3. Verifying Komisi password...")
    if verify_password(html_content):
        print("   OK: Password is '123'")
    else:
        print("   FAIL: Password is not '123'")
        all_passed = False

    # Verify frequency multipliers
    print("\n4. Verifying frequency multipliers...")
    if verify_frequency_multipliers(html_content):
        print("   OK: All frequency multipliers present")
    else:
        print("   FAIL: Missing frequency multipliers")
        all_passed = False

    # Verify terminology
    print("\n5. Verifying terminology...")
    has_syariah_terms = 'Uang Santunan' in html_content and 'Kontribusi' in html_content
    has_konven_terms = 'Uang Pertanggungan' in html_content and 'Premi' in html_content
    if has_syariah_terms and has_konven_terms:
        print("   OK: Both Syariah and Konvensional terminology present")
    else:
        print("   FAIL: Missing terminology")
        all_passed = False

    # Verify data unavailable message
    print("\n6. Verifying 'data tidak tersedia' handling...")
    if 'Data tidak tersedia' in html_content:
        print("   OK: 'Data tidak tersedia' message present")
    else:
        print("   FAIL: Missing data unavailable message")
        all_passed = False

    # Verify Berkah Kontribusi/Premi mode test
    print("\n7. Verifying Berkah budget mode (Rp 50Jt budget, age 40, PPP=5)...")
    key_berkah = 'IDR|B|M|40|5|110'
    rates_berkah = db.get(key_berkah)
    if rates_berkah:
        # Budget = 50,000,000
        # Walk through rates to find UP where premi <= budget
        budget = 50000000
        up_levels = [100000000,150000000,200000000,250000000,300000000,350000000,500000000,750000000,1000000000,5000000000]
        found_up = 0
        prev_up = 0
        prev_premi = 0
        for i in range(len(rates_berkah)):
            if rates_berkah[i] == 0:
                continue
            premi_at_level = rates_berkah[i] * 100000
            if premi_at_level <= budget:
                found_up = up_levels[i]
                prev_up = up_levels[i]
                prev_premi = premi_at_level
            else:
                if prev_premi > 0:
                    fraction = (budget - prev_premi) / (premi_at_level - prev_premi)
                    found_up = round(prev_up + fraction * (up_levels[i] - prev_up))
                break
        # Should be around 1 Miliar (since rate at 1Juta = 511.4 * 100K = 51.14Jt)
        # Actually rate at 750Juta = 383.6 * 100K = 38.36Jt, rate at 1M = 511.4 * 100K = 51.14Jt
        # Budget 50Jt is between 750Jt and 1M UP
        # fraction = (50M - 38.36M) / (51.14M - 38.36M) = 11.64 / 12.78 = 0.91
        # UP = 750M + 0.91 * (1000M - 750M) = 750M + 227.7M = ~977M
        expected_up_range = (900000000, 1050000000)  # Should be around 900M-1B
        if expected_up_range[0] <= found_up <= expected_up_range[1]:
            print(f"   OK: Budget Rp 50Jt -> UP ~Rp {found_up:,.0f} (within expected range)")
        else:
            print(f"   WARN: Budget Rp 50Jt -> UP ~Rp {found_up:,.0f} (expected {expected_up_range[0]:,.0f}-{expected_up_range[1]:,.0f})")
    else:
        print("   FAIL: Key not found")
        all_passed = False

    # Final summary
    print("\n" + "=" * 60)
    if all_passed:
        print("ALL VERIFICATIONS PASSED")
    else:
        print("SOME VERIFICATIONS FAILED")
    print("=" * 60)

    sys.exit(0 if all_passed else 1)


if __name__ == '__main__':
    main()
