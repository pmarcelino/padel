# Algarve Padel Market Research Tool

A Python-based data collection and analysis tool for identifying optimal locations for new padel facilities in Algarve, Portugal.

## Quick Start

```bash
# Clone repository
git clone <repository-url>
cd padel-research

# Run setup script
chmod +x setup.sh
./setup.sh

# Configure API key
# Edit .env and add your GOOGLE_API_KEY

# Run data collection
python scripts/collect_data.py

# Process data
python scripts/process_data.py

# Launch web app
streamlit run app/app.py
```

## Documentation

- [API Setup Guide](docs/API_SETUP.md) - Coming in Story 7.2
- [Usage Guide](docs/USAGE.md) - Coming in Story 7.2
- [Technical Design](technical-design.md)

## Requirements

- Python 3.10+
- Google Places API key

See [requirements.txt](requirements.txt) for full dependency list.

## License

MIT License (or your preferred license)

