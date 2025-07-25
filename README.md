# Pickleball Court Finder

A Python web scraper that finds pickleball courts using Google Places API and scrapes detailed information from pickleheads.com.

## Features

- **Google Places Integration**: Search for pickleball courts by zip code
- **Web Scraping**: Extract detailed court information from pickleheads.com
- **Cloudflare Bypass**: Robust scraping with anti-detection measures
- **Image Download**: Automatically download and store court images
- **Data Structure**: Organized court data with database-ready format

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/pickleball_finder.git
cd pickleball_finder
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create `.env` file:
```
Maps_API_KEY=your_google_maps_api_key_here
```

4. Add zip codes to `data/zip_codes.txt` (one per line)

## Usage

### Run Main Program
```bash
python main.py
```

### Debug Scraper
```bash
python debug_scraper.py
```

## Project Structure

```
pickleball_finder/
├── core/                 # Core functionality
├── scraper/             # Web scraping modules
├── models/              # Data models
├── utils/               # Utility functions
├── data/                # Data files
├── main.py              # Main application
└── debug_scraper.py     # Debug tool
```

## Data Extracted

- Court name
- Address and location link
- Phone number
- Website information
- Court images
- Geographic coordinates

## Requirements

- Python 3.8+
- Firefox browser
- Google Maps API key

## License

MIT License