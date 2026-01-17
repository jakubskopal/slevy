import json
import subprocess
import sys
from datetime import datetime

def main():
    # 1. Get runs
    print("Fetching workflow runs...")
    try:
        # Fetch status and conclusion to handle logic
        cmd = ["gh", "run", "list", "--json", "databaseId,createdAt,status,conclusion,workflowName", "--limit", "1000"]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        runs = json.loads(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"Error listing runs: {e.stderr}")
        sys.exit(1)
    except json.JSONDecodeError:
        print("Error parsing JSON from gh cli")
        sys.exit(1)

    print(f"Found {len(runs)} total runs.")

    # 2. Identify runs to delete
    # Sort by createdAt descending (newest first) just in case API didn't return them sorted
    runs.sort(key=lambda x: x['createdAt'], reverse=True)

    ids_to_delete = []
    # Track which workflows have we already found a success for
    found_success_per_workflow = set()

    for run in runs:
        run_id = str(run['databaseId'])
        status = run.get('status', '')       # e.g., 'completed', 'in_progress', 'queued'
        conclusion = run.get('conclusion', '') # e.g., 'success', 'failure', 'cancelled'
        workflow_name = run.get('workflowName', 'Unknown')

        # Rule: Keep all running (in_progress, queued, waiting, requested)
        if status in ['in_progress', 'queued', 'waiting', 'requested']:
            print(f"Keeping running workflow: {run_id} ({workflow_name}, {status})")
            continue

        # Rule: Only keep one successful PER WORKFLOW
        if conclusion == 'success':
            if workflow_name not in found_success_per_workflow:
                print(f"Keeping latest successful workflow: {run_id} ({workflow_name}, {run['createdAt']})")
                found_success_per_workflow.add(workflow_name)
                continue
            else:
                # Already have one success for this workflow type, delete this older one
                ids_to_delete.append(run_id)
                continue

        # Rule: Remove all failed, exclamation (cancelled), skipped, etc.
        # If we got here, it's not running, and it's not the first success.
        ids_to_delete.append(run_id)

    if not ids_to_delete:
        print("No runs to delete.")
        return

    # 3. Delete runs
    print(f"Deleting {len(ids_to_delete)} runs...")
    
    failed = 0
    success = 0
    
    for i, run_id in enumerate(ids_to_delete):
        if i % 10 == 0:
            print(f"Deleting progress: {i}/{len(ids_to_delete)}")
        try:
            subprocess.run(["gh", "run", "delete", run_id], check=True, capture_output=True)
            success += 1
        except subprocess.CalledProcessError as e:
            print(f"Failed to delete {run_id}: {e.stderr.decode().strip()}")
            failed += 1
            
    print(f"Done. Deleted: {success}, Failed: {failed}")

if __name__ == "__main__":
    main()
