#!/usr/bin/env python3
import os
import sys

# Add the parent directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Change to the backend directory
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# Import the module directly
import importlib.util
spec = importlib.util.spec_from_file_location("split_by_date", "split-by-date.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
app = module.app

if __name__ == '__main__':
    print("Starting Split-by-Date Backend Server...")
    print("Server will be available at: http://localhost:5001")
    print("API endpoint: http://localhost:5001/api/split-statement")
    print("")
    app.run(host='0.0.0.0', port=5001, debug=True)