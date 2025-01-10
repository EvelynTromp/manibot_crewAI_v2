V# ManiBot - Autonomous Prediction Market Trading Bot
## TLDR
- This is an autonomous trading bot that uses GPT-4 to analyze and trade on Manifold Markets
- Three main components:
  1. Researcher Agent: Gathers market data and relevant information
  2. Decision Maker Agent: Analyzes opportunities and calculates trades
  3. Executor Agent: Places trades and manages positions

Quick Setup:
```bash
git clone [repo]
pip install -r requirements.txt
# Add your API keys to .env:
MANIFOLD_API_KEY=your_key
OPENAI_API_KEY=your_key
GOOGLE_API_KEY=your_key
```

Basic Usage:
```bash
python main.py --scan        # Scan for opportunities
python main.py --market ID   # Analyze specific market
```

Key Settings (config/settings.py):
- MIN_BET_AMOUNT = 10
- MAX_BET_AMOUNT = 100
- MAX_SEARCH_RESULTS = 5
------------------------------------------------------------------------------------------------

## Features

- Autonomous market research and analysis
- Intelligent decision making using GPT-4
- Real-time market data monitoring
- Risk-managed trade execution
- Comprehensive reporting system
- Web search integration for market research
- Multi-agent architecture using CrewAI

## Important Notice

This bot deals with fake money on Manifold Markets (mana).

## Prerequisites

- Python 3.9+
- API Keys for:
  - Manifold Markets
  - OpenAI (GPT-4 access required)
  - Google Custom Search
- At least 100 M$ (Manifold dollars) for trading

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/manibot_crewAI_v2.git
cd manibot_crewAI_v2
```

2. Install dependencies:
```bash
pip install -r requirements.txt

3. Edit `settings.py` with your API keys:
```env
MANIFOLD_API_KEY=your_manifold_key
OPENAI_API_KEY=your_openai_key
GOOGLE_API_KEY=your_google_key
```

## Project Structure

```
manibot_crewAI_v2/
├── agents/              # CrewAI agents
│   ├── roles/          # Agent role definitions
│   ├── tools/          # Agent tools
│   ├── prompts/        # Agent prompts
├── crews/              # Crew definitions
├── tasks/              # Task definitions
├── core/               # Core functionality
├── utils/              # Utility functions
├── config/             # Configuration
└── main.py            # Entry point
```
## Usage
The bot supports two main modes of operation:
1. Scan markets for opportunities:
```bash
python main.py --scan
```

2. Analyze a specific market:
```bash
python main.py --market MARKET_ID
```

## Configuration

Key settings can be adjusted in `config/settings.py`:

```python
# Trading Parameters
MIN_BET_AMOUNT = 10
MAX_BET_AMOUNT = 100
MIN_PROBABILITY = 0.1
MAX_PROBABILITY = 0.9

# Research Configuration
MAX_SEARCH_RESULTS = 5
MAX_TOKENS = 4000

# Rate Limiting
MAX_CONCURRENT_SEARCHES = 3
MAX_RETRIES = 3
```

## Architecture

ManiBot uses a multi-agent architecture with three specialized agents:

1. **Researcher Agent**: Gathers market data and relevant information
   - Utilizes Google Custom Search for research
   - Analyzes market metrics and trading activity
   - Generates comprehensive research summaries

2. **Decision Maker Agent**: Analyzes opportunities and makes trading decisions
   - Evaluates market probabilities
   - Calculates optimal position sizes
   - Manages risk parameters

3. **Executor Agent**: Handles trade execution and position management
   - Places trades via Manifold API
   - Monitors active positions
   - Manages trade lifecycle

## Reporting

The bot generates detailed reports for each analysis session:
- Individual market analysis reports
- Consolidated scan reports
- Position monitoring reports
- Performance metrics

Reports are stored in the `reports/` directory, organized by date.

## Development Guide

To extend the bot's functionality:

1. Add new agent capabilities in `agents/roles/`
2. Define new tasks in `tasks/task_definitions.py`
3. Modify trading logic in `agents/roles/decision_maker.py`
4. Add new API integrations in `core/`


## Acknowledgments

- [CrewAI](https://github.com/joaomdmoura/crewai)
- [Manifold Markets](https://manifold.markets)
- [OpenAI](https://openai.com)
