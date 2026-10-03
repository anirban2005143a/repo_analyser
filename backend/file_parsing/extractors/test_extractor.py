import json
from file_parsing.extractors.PythonParser import PythonParser

file_path = r"D:\projects\repo_analyser\backend\file_parsing\test_codes\test.py"

with open(file_path, 'rb') as f:
    source_code = f.read()

extractor = PythonParser()

parse_code = extractor.parse(source_code=source_code)

json_output = json.dumps(parse_code, indent=2)

# Optional: Save the JSON output to a file for easier inspection
with open("parsed_tree.json", "w", encoding="utf-8") as f:
    f.write(json_output)