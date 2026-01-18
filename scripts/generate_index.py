import glob
import json
import os
import argparse

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", default="data", help="Directory containing data files")
    parser.add_argument("--target-dir", default="browser/public", help="Directory to write index.json")
    # Default changed to match the new processing pipeline
    parser.add_argument("--suffix", default="processed.json", help="Suffix of files to index (e.g. result.json, processed.json)")
    args = parser.parse_args()

    # Source directory
    DATA_DIR = args.data_dir
    # Target directory
    TARGET_DIR = args.target_dir
    SUFFIX = args.suffix
    
    # Ensure target exists
    os.makedirs(TARGET_DIR, exist_ok=True)
    
    index = {"sources": []}
    
    # Find all matching files
    # Note: glob pattern needs the dot if suffix doesn't have it, but usually we pass "processed.json"
    # so we glob for "*.processed.json"
    files = glob.glob(os.path.join(DATA_DIR, f"*.{SUFFIX}"))
    
    print(f"Found {len(files)} files with suffix '.{SUFFIX}' in {DATA_DIR}")
    
    for f in sorted(files):
        filename = os.path.basename(f)
        # Valid: kupi.processed.json -> name: kupi
        # We strip the full suffix ".processed.json"
        
        # Careful with replace if the name itself contains the suffix string, though unlikely for standard use.
        # Better to cut from the end
        if filename.endswith(f".{SUFFIX}"):
            name = filename[:-len(f".{SUFFIX}")]
        else:
            # Fallback (shouldn't happen due to glob)
            name = filename.replace(f".{SUFFIX}", "")
        
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
