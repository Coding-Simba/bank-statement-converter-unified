#\!/bin/bash

SERVER_IP="3.235.19.83"
KEY_PATH="/Users/MAC/Downloads/bank-statement-converter.pem"

ssh -i "$KEY_PATH" ubuntu@$SERVER_IP 'cd /home/ubuntu/bank-statement-converter/backend && python3 -c "
import sys
sys.path.insert(0, \".\")
print(\"Testing parsers...\")
print(\"=================\")

# List parser files
import os
print(\"\\nParser files:\")
for f in os.listdir(\".\"):
    if f.endswith(\"_parser.py\"):
        print(f\"  - {f}\")

# Try importing Westpac parser
try:
    from westpac_parser import parse_westpac
    print(\"\\n✅ Westpac parser imported\")
except Exception as e:
    print(f\"\\n❌ Westpac parser error: {e}\")

# Check if it inherits from base parser
try:
    import westpac_parser
    import inspect
    print(\"\\nWestpac parser info:\")
    print(f\"  - Module: {westpac_parser.__file__}\")
    if hasattr(westpac_parser, \"WestpacParser\"):
        print(\"  - Has WestpacParser class\")
        bases = inspect.getmro(westpac_parser.WestpacParser)
        print(f\"  - Inheritance: {[b.__name__ for b in bases]}\")
except Exception as e:
    print(f\"  - Error inspecting: {e}\")

# Check imports
try:
    with open(\"westpac_parser.py\", \"r\") as f:
        content = f.read()
        if \"from australian_bank_parser import\" in content:
            print(\"\\n⚠️  Westpac parser imports from australian_bank_parser\")
        if \"from .parsers.base_parser import\" in content:
            print(\"\\n⚠️  Westpac parser imports from .parsers.base_parser\")
        if \"def parse_westpac\" in content:
            print(\"\\n✅ Has parse_westpac function\")
except Exception as e:
    print(f\"\\nError reading parser: {e}\")
"'

