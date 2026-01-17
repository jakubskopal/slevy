import glob
import json
import os
import argparse

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", default="data", help="Directory containing result.json files")
    parser.add_argument("--target-dir", default="browser/public", help="Directory to write index.json")
    args = parser.parse_args()

    # Source directory
    DATA_DIR = args.data_dir
    # Target directory
    TARGET_DIR = args.target_dir
    
    # Ensure target exists
    os.makedirs(TARGET_DIR, exist_ok=True)
    
    index = {"sources": []}
    
    # Find all result files
    files = glob.glob(os.path.join(DATA_DIR, "*.result.json"))
    
    print(f"Found {len(files)} result files in {DATA_DIR}")
    
    for f in sorted(files):
        filename = os.path.basename(f)
        # Valid: kupi.result.json -> name: kupi
        name = filename.replace(".result.json", "")
        
        entry = {
            "name": name,
            "file": filename
        }
        index["sources"].append(entry)
        print(f"Added source: {name} -> {filename}")
        
    output_path = os.path.join(TARGET_DIR, "index.json")
    with open(output_path, "w") as f:
        json.dump(index, f, indent=2)
        
    print(f"Generated index at {output_path}")

if __name__ == "__main__":
    main()
