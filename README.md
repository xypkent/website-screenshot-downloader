# Website Batch Screenshot Tool

This is a powerful tool for batch capturing screenshots from various websites. The tool utilizes the Playwright automation framework, capable of handling modern web pages, including login processes, popup handling, and dynamic content loading.

## Features

- 🖼️ Batch download website screenshots from CSV files
- 🔐 Support for automatic login (handles websites requiring user authentication)
- 📂 Categorize screenshots into different folders based on the case_name field
- 🤖 Simulate real user behavior to reduce the chance of being blocked by website anti-scraping mechanisms
- 🔄 Automatically handle popups, cookie notifications, and other interfering elements
- 📱 Support for full-page screenshots
- 🛡️ Bypass common website anti-scraping detection mechanisms

## Directory Structure

```
website_screenshot_downloader/
├── README.md                    # This document
├── screenshot_downloader_enhanced.py  # Main program script
└── case_screenshots/           # Directory for categorized screenshot results
    ├── case1 90s Retro Business Card/
    ├── case2 Bakery ordering system/
    ├── case3 ExpensePlanner/
    └── ... (other case directories)
```

## Usage

### Environment Setup

1. Install Python 3.7+
2. Install necessary dependencies:

```bash
pip install pandas playwright tqdm
# Install Playwright browsers
playwright install chromium
```

### Basic Usage

1. **Batch Download Mode** (using a CSV file):

```bash
python screenshot_downloader_enhanced.py --csv your_file.csv --outdir output_directory_name
```

2. **Single URL Mode**:

```bash
python screenshot_downloader_enhanced.py --url https://example.com --output screenshot.png
```

### CSV File Format

The CSV file should contain the following columns:
- `prod_url`: Website URL (required)
- `case_name`: Case name (for grouping, optional)
- `site_type`: Website type (for filename generation, optional)

Example:
```
prod_url,case_name,site_type
https://example.com/page1,case1,Type1
https://example.com/page2,case1,Type2
https://another-site.com,case2,Type3
```

## Advanced Features

### Automatic Login

The script supports automatic login functionality. You can modify the username and password at the beginning of the script:

```python
USERNAME = "your_email@example.com"
PASSWORD = "your_password"
```

### Popup Handling

The script includes various methods to handle popups, cookie notifications, and other interfering elements on web pages, making screenshots cleaner.

### Execution Time Optimization

The script automatically skips existing screenshot files, facilitating resumption after interruptions.

## Notes

- The script uses headed mode by default to ensure better rendering
- To avoid being detected as a bot, the script simulates real user behavior (mouse movements, scrolling, etc.)
- For websites requiring login, ensure correct account information is provided

## License

MIT License