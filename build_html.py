#!/usr/bin/env python3
"""
Build the final MPS_Flexi_Updated.html by:
1. Preserving all HTML/CSS above <script>
2. Inserting the new JavaScript with embedded rate database
3. Preserving </body></html> at the end
"""

import subprocess
import json
import os

script_dir = os.path.dirname(os.path.abspath(__file__))

# Generate rate database
result = subprocess.run(
    ['python3', os.path.join(script_dir, 'generate_rate_db.py')],
    capture_output=True, text=True
)
rate_db_json = result.stdout.strip()

# Read the original HTML
html_path = os.path.join(script_dir, 'MPS_Flexi_Updated.html')
with open(html_path, 'r', encoding='utf-8') as f:
    html_content = f.read()

# Find the script section boundaries
script_start = html_content.find('<script>')
script_end = html_content.find('</script>') + len('</script>')

html_before_script = html_content[:script_start]
html_after_script = html_content[script_end:]

# Build the new JavaScript
new_js = f'''<script>
// ============================================================
// MPS Flexi Premium Calculator - Complete Rate Database
// ============================================================

const RATE_DB = {rate_db_json};

// UP Level arrays
const UP_LEVELS_IDR = [100000000,150000000,200000000,250000000,300000000,350000000,500000000,750000000,1000000000,5000000000];
const UP_LEVELS_USD = [100000,150000,200000,250000,300000,350000,500000,750000,1000000,5000000];

// Frequency multipliers
const FREQ_MULTIPLIERS = {{tahunan: 1, semesteran: 0.525, kuartalan: 0.275, bulanan: 0.095}};

// Minimum premi per plan
const MIN_PREMI = {{
    A: {{IDR: 4000000, USD: 400}},
    B: {{IDR: 5000000, USD: 500}},
    C: {{IDR: 5000000, USD: 500}}
}};

// Minimum UP
const MIN_UP = {{IDR: 100000000, USD: 10000}};

// ============================================================
// Core lookup function
// ============================================================
function getRates(currency, plan, gender, age, masaBayar, masaPerlindungan) {{
    var key = currency + "|" + plan + "|" + gender + "|" + age + "|" + masaBayar + "|" + masaPerlindungan;
    return RATE_DB[key] || null;
}}

// ============================================================
// Tab navigation
// ============================================================
function showTab(index) {{
    var tabs = document.querySelectorAll('.tabs li');
    var contents = document.querySelectorAll('.tab-content');
    for (var i = 0; i < tabs.length; i++) {{
        tabs[i].classList.remove('active');
        if (contents[i]) contents[i].classList.remove('active');
    }}
    tabs[index].classList.add('active');
    if (contents[index]) contents[index].classList.add('active');
    window.scrollTo({{top: 0, behavior: 'smooth'}});
}}

// ============================================================
// Komisi password check
// ============================================================
function checkKomisiPassword() {{
    var pwd = document.getElementById('komisi-pwd').value;
    if (pwd === '123') {{
        document.getElementById('komisi-lock').style.display = 'none';
        document.getElementById('komisi-content').style.display = 'block';
    }} else {{
        document.getElementById('komisi-error').style.display = 'block';
    }}
}}

// ============================================================
// Page initialization
// ============================================================
window.onload = function() {{
    var ageSelect = document.getElementById('calc-age');
    for (var i = 0; i <= 70; i++) {{
        var opt = document.createElement('option');
        opt.value = i;
        opt.text = i + " Tahun";
        if (i === 37) opt.selected = true;
        ageSelect.appendChild(opt);
    }}
    updateCalcUI();
    calculate();
}};

// ============================================================
// Format input nominal with thousand separators
// ============================================================
function formatInputNominal() {{
    var input = document.getElementById('calc-input-nominal');
    var val = input.value.replace(/\\D/g, '');
    if (val) {{
        input.value = parseFloat(val).toLocaleString('id-ID');
    }}
}}

// ============================================================
// Update calculator UI based on plan selection
// ============================================================
function updateCalcUI() {{
    var plan = document.getElementById('calc-plan').value;
    var mb = document.getElementById('calc-masabayar');
    var ml = document.getElementById('calc-masalindung');
    var methodContainer = document.getElementById('calc-method-container');
    var methodSelect = document.getElementById('calc-method');
    var methodLabel = methodContainer.querySelector('label');
    var currMb = mb.value;
    var currMl = ml.value;

    // Show method selector for ALL plans
    methodContainer.style.display = 'block';

    // Update terminology based on plan
    var isSyariah = (plan === 'A' || plan === 'B');
    var upTerm = isSyariah ? 'Uang Santunan' : 'Uang Pertanggungan';
    var premiTerm = isSyariah ? 'Kontribusi' : 'Premi';

    // Update method label
    methodLabel.innerHTML = '&#9881; Metode Penginputan';

    // Update method options
    methodSelect.innerHTML = '<option value="UP">Berdasarkan ' + upTerm + ' (UP)</option>' +
        '<option value="PREMI">Berdasarkan ' + premiTerm + '</option>';

    if (plan === 'A') {{
        mb.innerHTML = '<option value="1">1 Tahun (YRT)</option><option value="5">5 Tahun</option><option value="10">10 Tahun</option>';
        ml.innerHTML = '<option value="sama">Sama dengan masa bayar</option>';
        ml.disabled = true;
    }} else if (plan === 'B') {{
        mb.innerHTML = '<option value="5">5 Tahun</option><option value="10">10 Tahun</option><option value="15">15 Tahun</option>';
        ml.innerHTML = '<option value="110">Sampai Usia 110 Tahun</option>';
        ml.disabled = true;
    }} else if (plan === 'C') {{
        mb.innerHTML = '<option value="5">5 Tahun</option><option value="10">10 Tahun</option><option value="15">15 Tahun</option>';
        ml.disabled = false;

        // Restore mb value if possible
        if ([...mb.options].some(function(o) {{ return o.value === currMb; }})) {{
            mb.value = currMb;
        }}

        // Build masa perlindungan options based on masa bayar
        var currentMbVal = mb.value;
        ml.innerHTML = '';
        if (currentMbVal === '5' || currentMbVal === '10') {{
            ml.innerHTML += '<option value="15">15 Tahun</option>';
        }}
        ml.innerHTML += '<option value="25">25 Tahun</option><option value="35">35 Tahun</option>';

        // Restore ml value if possible
        if ([...ml.options].some(function(o) {{ return o.value === currMl; }})) {{
            ml.value = currMl;
        }}
    }}

    // Restore mb value if possible
    if ([...mb.options].some(function(o) {{ return o.value === currMb; }})) {{
        mb.value = currMb;
    }}

    updateMinInfo();
}}

// ============================================================
// Update minimum info display
// ============================================================
function updateMinInfo() {{
    var currency = document.getElementById('calc-currency').value;
    var method = document.getElementById('calc-method').value;
    var plan = document.getElementById('calc-plan').value;
    var info = document.getElementById('min-info');
    var label = document.getElementById('label-nominal');

    var isSyariah = (plan === 'A' || plan === 'B');
    var upTerm = isSyariah ? 'Uang Santunan' : 'Uang Pertanggungan';
    var premiTerm = isSyariah ? 'Kontribusi' : 'Premi';

    if (method === 'UP') {{
        label.innerText = upTerm + ' (UP)';
        info.innerText = currency === 'IDR' ? 'Minimum UP Rp 100.000.000' : 'Minimum UP USD 10.000';
    }} else {{
        label.innerText = 'Target ' + premiTerm + ' Tahunan';
        var minP = MIN_PREMI[plan][currency];
        if (currency === 'IDR') {{
            info.innerText = 'Minimum ' + premiTerm + ' Rp ' + minP.toLocaleString('id-ID');
        }} else {{
            info.innerText = 'Minimum ' + premiTerm + ' USD ' + minP.toLocaleString('en-US');
        }}
    }}
}}

// ============================================================
// Main calculation function
// ============================================================
function calculate() {{
    var plan = document.getElementById('calc-plan').value;
    var gender = document.getElementById('calc-gender').value;
    var age = parseInt(document.getElementById('calc-age').value);
    var currency = document.getElementById('calc-currency').value;
    var method = document.getElementById('calc-method').value;
    var mb = document.getElementById('calc-masabayar').value;
    var mlSelect = document.getElementById('calc-masalindung').value;
    var paymentMode = parseFloat(document.getElementById('calc-payment-mode').value);

    var isSyariah = (plan === 'A' || plan === 'B');
    var upTerm = isSyariah ? 'Uang Santunan' : 'Uang Pertanggungan';
    var premiTerm = isSyariah ? 'Kontribusi' : 'Premi';

    // Determine masa perlindungan for lookup
    var masaPerlindungan;
    if (plan === 'A') {{
        // For Amanah: masa perlindungan = Term = YRT/5/10
        if (mb === '1') {{
            masaPerlindungan = 'YRT';
        }} else {{
            masaPerlindungan = mb;
        }}
    }} else if (plan === 'B') {{
        masaPerlindungan = '110';
    }} else {{
        masaPerlindungan = mlSelect;
    }}

    // Gender mapping
    var genderShort = (gender === 'pria') ? 'M' : 'F';

    // Get rates from database
    var rates = getRates(currency, plan, genderShort, age, mb, masaPerlindungan);

    // UP levels for current currency
    var upLevels = (currency === 'IDR') ? UP_LEVELS_IDR : UP_LEVELS_USD;

    // IDR multiplier: rate * 100000 = annual premi; USD: rate * 1 = annual premi
    var rateMultiplier = (currency === 'IDR') ? 100000 : 1;

    var rawInput = document.getElementById('calc-input-nominal').value.replace(/\\D/g, '');
    var nominal = parseFloat(rawInput) || 0;

    var resultPremiTahunan = 0;
    var resultUP = 0;
    var warningText = "";
    var dataUnavailable = false;

    // Check if rates exist
    if (!rates || rates.every(function(r) {{ return r === 0; }})) {{
        dataUnavailable = true;
        warningText = "&#9888; Data tidak tersedia untuk kombinasi ini.";
    }} else if (method === 'UP') {{
        // UP mode: user enters UP, calculate premi
        resultUP = nominal;

        if (resultUP <= 0) {{
            resultPremiTahunan = 0;
        }} else if (resultUP < upLevels[0]) {{
            // Below minimum UP level - extrapolate from first level
            var baseRate = rates[0];
            if (baseRate === 0) {{
                dataUnavailable = true;
                warningText = "&#9888; Data tidak tersedia untuk kombinasi ini.";
            }} else {{
                var premiPerUnit = baseRate * rateMultiplier / upLevels[0];
                resultPremiTahunan = Math.round(premiPerUnit * resultUP);
            }}
        }} else if (resultUP >= upLevels[9]) {{
            // At or above max level
            var baseRate = rates[9];
            if (baseRate === 0) {{
                dataUnavailable = true;
                warningText = "&#9888; Data tidak tersedia untuk UP sebesar ini.";
            }} else {{
                var premiPerUnit = baseRate * rateMultiplier / upLevels[9];
                resultPremiTahunan = Math.round(premiPerUnit * resultUP);
            }}
        }} else {{
            // Find bracket
            var lowerIdx = 0;
            for (var i = 0; i < upLevels.length - 1; i++) {{
                if (resultUP >= upLevels[i]) lowerIdx = i;
            }}
            var upperIdx = lowerIdx + 1;

            if (resultUP === upLevels[lowerIdx]) {{
                // Exact match
                if (rates[lowerIdx] === 0) {{
                    dataUnavailable = true;
                    warningText = "&#9888; Data tidak tersedia untuk kombinasi ini.";
                }} else {{
                    resultPremiTahunan = Math.round(rates[lowerIdx] * rateMultiplier);
                }}
            }} else {{
                // Interpolate between two levels
                var lowerRate = rates[lowerIdx];
                var upperRate = rates[upperIdx];
                if (lowerRate === 0 || upperRate === 0) {{
                    dataUnavailable = true;
                    warningText = "&#9888; Data tidak tersedia untuk kombinasi ini.";
                }} else {{
                    var lowerPremi = lowerRate * rateMultiplier;
                    var upperPremi = upperRate * rateMultiplier;
                    var fraction = (resultUP - upLevels[lowerIdx]) / (upLevels[upperIdx] - upLevels[lowerIdx]);
                    resultPremiTahunan = Math.round(lowerPremi + fraction * (upperPremi - lowerPremi));
                }}
            }}
        }}

        // Validate minimum UP
        var minUP = MIN_UP[currency];
        if (!dataUnavailable && resultUP > 0 && resultUP < minUP) {{
            warningText += "&#9888; Peringatan: " + upTerm + " di bawah minimum (" +
                (currency === 'IDR' ? 'Rp ' + minUP.toLocaleString('id-ID') : 'USD ' + minUP.toLocaleString('en-US')) + ").<br>";
        }}

        // Validate minimum premi
        var minPremi = MIN_PREMI[plan][currency];
        if (!dataUnavailable && resultPremiTahunan > 0 && resultPremiTahunan < minPremi) {{
            warningText += "&#9888; Peringatan: " + premiTerm + " tahunan di bawah minimum (" +
                (currency === 'IDR' ? 'Rp ' + minPremi.toLocaleString('id-ID') : 'USD ' + minPremi.toLocaleString('en-US')) + ").<br>";
        }}

    }} else {{
        // PREMI mode: user enters annual budget, find max UP
        var budget = nominal;
        resultPremiTahunan = budget;

        if (budget <= 0) {{
            resultUP = 0;
        }} else {{
            // Walk through rate array to find which UP level fits the budget
            var foundUP = 0;
            var prevUP = 0;
            var prevPremi = 0;

            for (var i = 0; i < rates.length; i++) {{
                if (rates[i] === 0) continue;
                var premiAtLevel = rates[i] * rateMultiplier;
                if (premiAtLevel <= budget) {{
                    foundUP = upLevels[i];
                    prevUP = upLevels[i];
                    prevPremi = premiAtLevel;
                }} else {{
                    // Budget is between previous level and this level
                    if (prevPremi > 0 && prevUP > 0) {{
                        var fraction = (budget - prevPremi) / (premiAtLevel - prevPremi);
                        foundUP = Math.round(prevUP + fraction * (upLevels[i] - prevUP));
                    }} else {{
                        // Budget below the first available level - extrapolate down
                        var premiPerUnit = premiAtLevel / upLevels[i];
                        foundUP = Math.round(budget / premiPerUnit);
                    }}
                    break;
                }}
            }}

            // If budget exceeds all levels, extrapolate from the last one
            if (foundUP === prevUP && prevPremi > 0 && prevPremi <= budget) {{
                var lastIdx = -1;
                for (var i = rates.length - 1; i >= 0; i--) {{
                    if (rates[i] !== 0) {{ lastIdx = i; break; }}
                }}
                if (lastIdx >= 0) {{
                    var premiPerUnit = rates[lastIdx] * rateMultiplier / upLevels[lastIdx];
                    foundUP = Math.round(budget / premiPerUnit);
                }}
            }}

            resultUP = foundUP;
        }}

        // Validate minimum premi
        var minPremi = MIN_PREMI[plan][currency];
        if (!dataUnavailable && budget > 0 && budget < minPremi) {{
            warningText += "&#9888; Peringatan: " + premiTerm + " tahunan di bawah minimum (" +
                (currency === 'IDR' ? 'Rp ' + minPremi.toLocaleString('id-ID') : 'USD ' + minPremi.toLocaleString('en-US')) + ").<br>";
        }}

        // Validate minimum UP
        var minUP = MIN_UP[currency];
        if (!dataUnavailable && resultUP > 0 && resultUP < minUP) {{
            warningText += "&#9888; Peringatan: " + upTerm + " di bawah minimum (" +
                (currency === 'IDR' ? 'Rp ' + minUP.toLocaleString('id-ID') : 'USD ' + minUP.toLocaleString('en-US')) + ").<br>";
        }}
    }}

    // Apply frequency multiplier for display
    var finalPremi = Math.round(resultPremiTahunan * paymentMode);

    // Display results
    var currSymbol = (currency === 'IDR') ? 'Rp ' : '$ ';

    if (dataUnavailable) {{
        document.getElementById('result-label').innerText = premiTerm + '/' + upTerm;
        document.getElementById('calc-premium').innerHTML = '<span style="color:#e53935;font-size:1.2rem">Data tidak tersedia</span>';
        document.getElementById('calc-detail').innerHTML = '';
    }} else if (method === 'UP') {{
        document.getElementById('result-label').innerText = premiTerm;
        document.getElementById('calc-premium').innerHTML = currSymbol + finalPremi.toLocaleString('id-ID');
    }} else {{
        document.getElementById('result-label').innerText = upTerm;
        document.getElementById('calc-premium').innerHTML = currSymbol + resultUP.toLocaleString('id-ID');
    }}

    // Build detail line
    if (!dataUnavailable) {{
        var modeText = "Tahunan";
        if (paymentMode === 0.525) modeText = "Semesteran";
        if (paymentMode === 0.275) modeText = "Kuartalan";
        if (paymentMode === 0.095) modeText = "Bulanan";

        var strML;
        if (plan === 'A') {{
            strML = (mb === '1') ? 'YRT (1 Tahun)' : mb + ' Tahun';
        }} else if (plan === 'B') {{
            strML = 'Hingga Usia 110';
        }} else {{
            strML = mlSelect + ' Tahun';
        }}

        var genderDisplay = (gender === 'pria') ? 'PRIA' : 'WANITA';
        var planName = (plan === 'A') ? 'Amanah' : (plan === 'B') ? 'Berkah' : 'Cermat';

        document.getElementById('calc-detail').innerHTML =
            '<strong>Profil:</strong> ' + genderDisplay + ', ' + age + ' Tahun | <strong>Plan:</strong> ' + planName + '<br>' +
            '<strong>Masa Bayar:</strong> ' + mb + ' Tahun | <strong>Masa Perlindungan:</strong> ' + strML + '<br>' +
            '<strong>Pembayaran ' + modeText + ':</strong> ' + currSymbol + finalPremi.toLocaleString('id-ID') + ' / periode.<br>' +
            '<strong>' + upTerm + ':</strong> ' + currSymbol + resultUP.toLocaleString('id-ID');
    }}

    document.getElementById('calc-note').innerHTML = warningText;
}}
</script>'''

# Assemble final HTML
final_html = html_before_script + new_js + html_after_script

# Write output
with open(html_path, 'w', encoding='utf-8') as f:
    f.write(final_html)

print(f"HTML rebuilt successfully. File size: {len(final_html)} bytes")
print(f"Rate DB entries: {len(json.loads(rate_db_json))}")
