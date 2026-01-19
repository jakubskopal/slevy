#!/bin/bash
set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}finding latest successful 'deploy.yml' run...${NC}"

# 0. Get Repo Name
REPO=$(gh repo view --json nameWithOwner -q .nameWithOwner)
echo -e "${BLUE}Repository: $REPO${NC}"

# 1. Identify the latest successful run of the 'deploy.yml' workflow
LATEST_RUN_ID=$(gh run list --workflow=deploy.yml --status=success --limit=1 --json databaseId --jq '.[0].databaseId')

if [ -z "$LATEST_RUN_ID" ]; then
  echo -e "${RED}No successful run found.${NC}"
  exit 1
fi

echo -e "${GREEN}Found latest run ID: $LATEST_RUN_ID${NC}"

# 2. Get Artifacts List
echo -e "${BLUE}Fetching artifacts list...${NC}"
ARTIFACTS_JSON=$(gh api "/repos/$REPO/actions/runs/$LATEST_RUN_ID/artifacts")

# 3. Define the list of stores/artifacts we expect
STORES=("albert" "billa" "globus" "tesco" "kupi")

# 4. Iterate and download
for STORE in "${STORES[@]}"; do
  ARTIFACT_NAME="raw-${STORE}"
  TARGET_DIR="data/${STORE}_raw"
  
  echo -e "${BLUE}Processing $STORE...${NC}"
  
  # Find latest non-expired artifact ID
  # We select based on name, ensure it is not expired, sort by created_at desc, and pick the first one.
  ARTIFACT_ID=$(echo "$ARTIFACTS_JSON" | jq -r "[.artifacts[] | select(.name == \"$ARTIFACT_NAME\" and .expired == false)] | sort_by(.created_at) | reverse | .[0].id")
  
  if [ -z "$ARTIFACT_ID" ] || [ "$ARTIFACT_ID" == "null" ]; then
      echo -e "  ${RED}No valid (non-expired) artifact found for $ARTIFACT_NAME in run $LATEST_RUN_ID${NC}"
      continue
  fi

  echo "  Found Artifact ID: $ARTIFACT_ID"
  
  # Ensure target directory exists
  mkdir -p "$TARGET_DIR"
  
  echo "  Downloading zip..."
  if gh api "/repos/$REPO/actions/artifacts/$ARTIFACT_ID/zip" > "${ARTIFACT_NAME}.zip"; then
      echo "  Unzipping to $TARGET_DIR..."
      unzip -o -q "${ARTIFACT_NAME}.zip" -d "$TARGET_DIR"
      rm "${ARTIFACT_NAME}.zip"
      echo -e "  ${GREEN}Success${NC}"
  else
      echo -e "  ${RED}Download failed${NC}"
      rm -f "${ARTIFACT_NAME}.zip"
  fi
  
done

echo -e "${GREEN}Download complete.${NC}"
