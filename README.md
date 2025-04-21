# AI Web Scraping Agent

An autonomous agent that takes a URL, scrapes specified data, processes it, and saves it to Excel files. The agent operates independently by creating processing containers for each scraping job.

## Features

- **Autonomous Operation**: Agent acts independently to fetch, process, and store data
- **Isolated Containers**: Creates scraping containers for each job to isolate processing
- **Anti-Bot Protection Bypass**: Uses rotating user agents, request delays, and proxy services
- **Intelligent Data Processing**: Automatically detects data types and cleans raw data
- **Multiple Output Formats**: Saves data to Excel, CSV, and JSON formats
- **Command Line Interface**: Easy-to-use CLI for creating and managing scraping jobs

## Installation

1. Clone this repository:
```bash
git clone https://github.com/SlayerK15/Web_Scraping_Agent.git
cd web_scraping_agent
```

2. Install the required dependencies:
```bash
pip install -r requirements.txt
```

3. Create necessary directories (if not present):
```bash
mkdir -p logs data output containers
```

## Usage

### Command Line Interface

The agent can be used from the command line:

```bash
# Create a new scraping job
python cli.py create --url "https://example.com/products" --selector-file selectors/product_listing.json --name "Example Products"

# Execute a scraping job
python cli.py execute --job-id <job_id>

# Check job status
python cli.py status --job-id <job_id>

# List all jobs
python cli.py list

# Create and execute in one command
python cli.py run --url "https://example.com/products" --selector-file selectors/product_listing.json --name "Example Products"
```

### Using in Python Scripts

```python
from agent import WebScraperAgent

# Initialize the agent
agent = WebScraperAgent()

# Create a job
job_id = agent.create_scraping_job(
    url="https://example.com/products",
    selectors=selector_config,
    job_name="Example Products"
)

# Execute the job
success = agent.execute_job(job_id)
```

## Creating Selector Files

Selector files define what data to extract and are in JSON format. The agent includes example selectors in the `selectors/` directory.

Example product listing selector:
```json
{
  "type": "css",
  "selector": ".product-item",
  "extract": {
    "product_name": {
      "type": "text",
      "selector": ".product-title"
    },
    "price": {
      "type": "text",
      "selector": ".product-price"
    }
  }
}
```

## Using Proxy Services

For websites with anti-scraping protection, the agent can use proxy services:

1. Add your API key to `config/default_config.json`:
```json
{
  "scraping": {
    "use_proxy": true,
    "proxy_service": "scraperapi",
    "proxy_api_key": "your_api_key_here"
  }
}
```

2. Multiple proxy services are supported in `config/proxy_services.json`

## Advanced Configuration

See the `config/` directory for configuration options:

- `default_config.json`: General agent configuration
- `proxy_services.json`: Configuration for various proxy services

## Project Structure

```
web_scraping_agent/
├── agent.py                   # Main agent class
├── scraper_container.py       # Container for scraping
├── data_processor.py          # Data processing module
├── cli.py                     # Command-line interface
├── config/                    # Configuration files
├── selectors/                 # Selector definitions
├── containers/                # Job information storage
├── data/                      # Raw scraped data
├── output/                    # Processed output files
└── logs/                      # Log files
```

## License

MIT License