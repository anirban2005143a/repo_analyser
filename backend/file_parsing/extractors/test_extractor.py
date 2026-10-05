import json
from file_parsing.extractors.PythonParser import PythonParser
from file_parsing.extractors.JavaScriptParser import JavaScriptParser

file_path = r"D:\projects\repo_analyser\backend\file_parsing\test_codes\scheduler.worker.js"

with open(file_path, 'rb') as f:
    source_code = f.read()

extractor = JavaScriptParser()

parse_code = extractor.parse(source_code=source_code)

json_output = json.dumps(parse_code, indent=2)

# Optional: Save the JSON output to a file for easier inspection
with open("parsed_tree.json", "w", encoding="utf-8") as f:
    f.write(json_output)