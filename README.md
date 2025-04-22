# Web Scraper AI

An AI-powered web scraper that automatically generates CSS selectors for data extraction. This tool simplifies the web scraping process by only requiring the user to provide a URL and describe what data they want to extract.

## Features

- **AI-Powered Selector Generation**: Uses Anthropic or OpenAI APIs to generate CSS selectors based on natural language descriptions
- **Automatic Scraper**: Handles the complete scraping process with minimal user input
- **Containerized Execution**: Runs in Docker containers for isolation and reproducibility
- **Proxy Rotation**: Built-in proxy support to avoid IP blocking
- **DNS Protection**: Implements DNS protection strategies to avoid bans
- **Feedback Learning**: Uses user feedback to improve selector generation over time
- **Multiple Export Formats**: Export data as CSV, Excel, or JSON
- **CLI Interface**: Easy-to-use command-line interface

## Installation

### Prerequisites

- Python 3.7+
- Docker (optional, for containerized execution)
- Anthropic or OpenAI API key

### Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/web-scraper-ai.git
   cd web-scraper-ai
   ```

2. Create a virtual environment and install dependencies:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. Set up environment variables:
   ```bash
   cp .env.example .env
   ```
   
   Edit the `.env` file to add your API keys:
   ```
   ANTHROPIC_API_KEY=your_anthropic_api_key
   # or
   OPENAI_API_KEY=your_openai_api_key
   
   # Optional proxy service API keys
   BRIGHTDATA_API_KEY=your_brightdata_api_key
   SCRAPERAPI_API_KEY=your_scraperapi_api_key
   ZYTE_API_KEY=your_zyte_api_key
   ```

4. (Optional) Install the package:
   ```bash
   pip install -e .
   ```

## Usage

### Command Line Interface

The scraper can be used directly from the command line:

```bash
# Basic usage
python -m main --url https://example.com --data "product titles and prices" --pages 3

# Specify output format
python -m main --url https://example.com --data "product titles and prices" --format excel

# Specify output path
python -m main --url https://example.com --data "product titles and prices" --output my_data.csv
```

### CLI Commands

The CLI provides several commands:

```bash
# Scrape a website
webscraper scrape --url https://example.com --data "product titles and prices"

# List saved selectors
webscraper list-selectors

# Show details of a specific selector
webscraper show-selector --id <selector_id>

# Delete a selector
webscraper delete-selector --id <selector_id>
```

### Using Docker

The scraper can also be run in a Docker container:

```bash
# Build the Docker image
cd web-scraper-ai
docker build -t web-scraper-ai -f docker/Dockerfile .

# Run the container
docker run -it --rm \
  -v $(pwd)/storage:/app/storage \
  -v $(pwd)/logs:/app/logs \
  -e ANTHROPIC_API_KEY=your_anthropic_api_key \
  web-scraper-ai \
  python -m main --url https://example.com --data "product titles and prices"
```

Alternatively, use Docker Compose:

```bash
# Set environment variables in .env file first
cd web-scraper-ai
docker-compose -f docker/docker-compose.yml up
```

## Configuration

Configuration files are stored in the `config` directory:

- `settings.json`: General settings
- `ai_config.json`: AI service configuration
- `scraper_config.json`: Scraper configuration

You can modify these files to customize the behavior of the scraper.

## Project Structure

```
web-scraper-ai/
│
├── agent/                  # AI agent and selector generation
├── scraper/                # Web scraping implementation
├── data/                   # Data processing and export
├── docker/                 # Docker configuration
├── config/                 # Configuration files
├── storage/                # Data storage
├── cli/                    # Command-line interface
├── utils/                  # Utility functions
├── tests/                  # Unit tests
│
├── main.py                 # Main entry point
├── setup.py                # Package setup
└── requirements.txt        # Python dependencies
```

## API Keys and Proxy Services

To use this scraper, you need at least one of:

- Anthropic API key (for Claude models)
- OpenAI API key (for GPT models)

For better scraping performance, you can use proxy services:

- BrightData (formerly Luminati)
- ScraperAPI
- Zyte (formerly Scrapy Cloud)

## Troubleshooting

### Common Issues

- **No data scraped**: This might indicate that the selectors couldn't locate the data. Try regenerating selectors with a more detailed description.
- **Blocked by the website**: Use a proxy service to avoid IP blocking.
- **Slow scraping speed**: Adjust the delay settings in the configuration.

### Debug Mode

Run the scraper in debug mode for more detailed logs:

```bash
python -m main --url https://example.com --data "product titles and prices" --debug
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.