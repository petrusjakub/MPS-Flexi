"""
Inject the extracted premium data into MPS_Flexi_Updated.html.
Replaces only the dataPremiJSON array content.
"""

import json
import sys

# First, extract the premium data
exec(open('extract_premi.py').read())

# Format as compact JSON array entries, one per line
lines_js = []
for e in entries:
    lines_js.append('  ' + json.dumps(e, separators=(',', ':')))

new_array_content = 'const dataPremiJSON = [\n' + ',\n'.join(lines_js) + '\n];'

# Read the HTML file
with open('MPS_Flexi_Updated.html', 'r', encoding='utf-8') as f:
    html = f.read()

# Find and replace the dataPremiJSON array
start_marker = 'const dataPremiJSON = ['
end_marker = '];'

start_idx = html.find(start_marker)
if start_idx == -1:
    print("ERROR: Could not find start marker 'const dataPremiJSON = ['")
    sys.exit(1)

# Find the closing ]; after the start
end_idx = html.find(end_marker, start_idx)
if end_idx == -1:
    print("ERROR: Could not find end marker '];'")
    sys.exit(1)

# Include the ]; in the replacement
end_idx += len(end_marker)

# Replace
new_html = html[:start_idx] + new_array_content + html[end_idx:]

# Write back
with open('MPS_Flexi_Updated.html', 'w', encoding='utf-8') as f:
    f.write(new_html)

print(f"SUCCESS: Injected {len(entries)} entries into dataPremiJSON")
print(f"HTML file size: {len(new_html)} bytes ({len(new_html)/1024:.1f} KB)")
