# CyberAutoGenAI

A comprehensive security analysis system using AutoGen and various security APIs.

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/CyberAutoGenAi.git
cd CyberAutoGenAi
```

2. Create and activate virtual environment:

For macOS/Linux:
```bash
python -m venv venv
source venv/bin/activate
```

For Windows:
```bash
python -m venv venv
.\venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -e .
```

4. Create a `.env` file with your API keys:
```bash
VIRUSTOTAL_API_KEY=your_virustotal_api_key
SHODAN_API_KEY=your_shodan_api_key
ABUSEIPDB_API_KEY=your_abuseipdb_api_key
```

## Usage

1. Start the MCP server:
```bash
python -m cyberautogenai.mcp.server
```

2. In a new terminal, start the Streamlit UI:
```bash
streamlit run cyberautogenai/ui/app.py
```

## Development

- Format code: `black .`
- Sort imports: `isort .`
- Run linter: `flake8`
- Run tests: `pytest`

## License

MIT License 