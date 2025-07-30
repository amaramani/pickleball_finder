# Pickleball Court Scraper

A Python application that scrapes pickleball court information from pickleheads.com and saves it to CSV format.

## Features

- **Google Places Integration**: Find courts by zip code using Google Places API
- **Web Scraping**: Extract court names, addresses, and links from pickleheads.com
- **CSV Export**: Save court data in structured CSV format
- **Clean Architecture**: Modular design with separation of concerns

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

Run the scraper:
```bash
python main.py
```

## Output

The application creates a CSV file at `data/pickleball_courts.csv` with columns:
- **Name**: Court name
- **Address**: Court address
- **Courtlink**: Link to court page on pickleheads.com

## Project Structure

```
pickleball_finder/
├── core/                    # Core business logic
│   ├── court_finder.py      # Find court URLs by zip code
│   ├── court_scraper.py     # Scrape individual court data
│   ├── google_places_api.py # Google Places API integration
│   └── data_processor.py    # Process Google Places data
├── scraper/                 # Web scraping components
│   └── pickleheads_scraper.py
├── models/                  # Data models
│   └── scraped_court_data.py
├── utils/                   # Utility functions
│   ├── config.py
│   ├── performance_helpers.py
│   ├── scraping_helpers.py
│   └── url_formatter.py
├── data/                    # Data files
│   ├── zip_codes.txt        # Input zip codes
│   └── pickleball_courts.csv # Output CSV
└── main.py                  # Main application
```

## Requirements

- Python 3.8+
- Firefox browser (for web scraping)
- Google Maps API key

## License

MIT License