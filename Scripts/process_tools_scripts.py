import os
import re
from pathlib import Path

def remove_empty_process_function(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Regex pattern to match empty processDataFrame functions
    pattern = re.compile(
        r"\n\s*def processDataFrame\(self, dataFrame, argsList\):\s*\n\s*return dataFrame\s*\n",
        re.MULTILINE
    )
    
    new_content = re.sub(pattern, '\n', content)  # Remove the function, keeping line breaks clean
    
    if new_content != content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"Updated: {file_path}")

def main():
    base_dir = "/Users/amasson/Travail/bioimageit/PyFlow/Tools"
    
    for tool_folder in sorted(list(Path(base_dir).iterdir())):
        if not tool_folder.is_dir(): continue
        for file in sorted(list(tool_folder.iterdir())):
            if file.suffix == ".py":
                remove_empty_process_function(file)

if __name__ == "__main__":
    main()