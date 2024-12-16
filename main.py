import asyncio
import argparse
from crews.market_crew import MarketCrew
from utils.logger import get_logger
from config.settings import settings

logger = get_logger(__name__)

async def main():
    parser = argparse.ArgumentParser(description='ManifoldBot - Autonomous Trading Bot')
    parser.add_argument('--scan', action='store_true', help='Scan markets for opportunities')
    parser.add_argument('--market', type=str, help='Analyze specific market ID')
    parser.add_argument('--monitor', action='store_true', help='Monitor active positions')
    args = parser.parse_args()

    logger.info("Starting bot...")
    crew = MarketCrew()
    logger.info("Crew initialized successfully")
    
    try:
        if args.scan:
            logger.info("Scanning markets for opportunities...")
            results = await crew.scan_markets()
            logger.info(f"Scan complete. Results: {results}")
            
        elif args.market:
            logger.info(f"Analyzing specific market: {args.market}")
            result = await crew.analyze_and_trade(args.market)
            logger.info(f"Analysis complete. Result: {result}")
            
        elif args.monitor:
            logger.info("Monitoring active positions...")
            positions = await crew.monitor_positions()
            logger.info(f"Current positions: {positions}")
            
        else:
            logger.error("No action specified. Use --scan, --market, or --monitor")
            
    except Exception as e:
        logger.error(f"Error in main execution: {str(e)}")
        raise

if __name__ == "__main__":
    asyncio.run(main())