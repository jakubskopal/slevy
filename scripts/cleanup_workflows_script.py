import json
import subprocess
import sys
from datetime import datetime, timedelta, timezone

def main():
    # 1. Get runs
    print("Fetching workflow runs...")
    try:
        # Get all runs (limit 1000 to be safe)
        cmd = ["gh", "run", "list", "--json", "databaseId,createdAt", "--limit", "1000"]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        runs = json.loads(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"Error listing runs: {e.stderr}")
        sys.exit(1)
    except json.JSONDecodeError:
        print("Error parsing JSON from gh cli")
        sys.exit(1)

    print(f"Found {len(runs)} total runs.")

    # 2. Filter runs
    # UTC now check
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(hours=12)
    
    ids_to_delete = []
    
    for run in runs:
        # 2026-01-17T01:48:04Z or similar
        # Python 3.11+ method, safely handles Z
        created_str = run['createdAt'].replace('Z', '+00:00')
        try:
            created_at = datetime.fromisoformat(created_str)
            if created_at < cutoff:
                ids_to_delete.append(str(run['databaseId']))
        except ValueError as e:
            print(f"Error parsing date {created_str}: {e}")

    print(f"Found {len(ids_to_delete)} runs older than {cutoff} (12 hours ago).")

    if not ids_to_delete:
        print("No runs to delete.")
        return

    # 3. Delete runs
    print(f"Deleting {len(ids_to_delete)} runs...")
    
    failed = 0
    success = 0
    
    for i, run_id in enumerate(ids_to_delete):
        if i % 10 == 0:
            print(f"Progress: {i}/{len(ids_to_delete)}")
        try:
            subprocess.run(["gh", "run", "delete", run_id], check=True, capture_output=True)
            success += 1
        except subprocess.CalledProcessError as e:
            print(f"Failed to delete {run_id}: {e.stderr.decode().strip()}")
            failed += 1
            
    print(f"Done. Deleted: {success}, Failed: {failed}")

if __name__ == "__main__":
    main()
