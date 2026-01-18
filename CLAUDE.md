# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Documentation

Read `README.md` for detailed project architecture, data schema, crawler strategies, processing pipeline, and deployment workflow.

## Quick Reference Commands

### Python
```bash
source venv/bin/activate
pip install -r requirements.txt
python sources/crawl_<store>.py --headless --workers 4
python sources/parse_<store>.py --workers 4
```

### Processing Pipeline
```bash
./scripts/processing --default
```

### Browser App
```bash
cd browser
nvm use  # Required: Node v25.2.1
npm install
npm run dev
npm run build
npm run lint
```

## Key Files

- `sources/schema.json` - Output data schema
- `sources/<store>/crawler.py` and `parser.py` - Store-specific implementations
- `processing/*.py` - Pipeline transformation steps
- `.github/workflows/deploy.yml` - CI/CD matrix (update when adding new stores)
