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
            print("\n🔍 Scanning markets for opportunities...\n")  # More user-friendly
            results = await crew.scan_markets()
            
            # Format results in a cleaner way
            successful = len([r for r in results if r.get('success')])
            total = len(results)
            print(f"\n✅ Scan complete: Analyzed {total} markets ({successful} successful)\n")
            
        elif args.market:
            print(f"\n📊 Analyzing market: {args.market}\n")
            result = await crew.analyze_and_trade(args.market)
            print("\n✅ Analysis complete\n")
            
        elif args.monitor:
            print("\n👀 Monitoring active positions...\n")
            positions = await crew.monitor_positions()
            print(f"\nCurrent positions: {positions}\n")
            
        else:
            print("\n❌ Error: No action specified. Use --scan, --market, or --monitor\n")
            
    except Exception as e:
        print(f"\n❌ Error: {str(e)}\n")
        raise



if __name__ == "__main__":
    asyncio.run(main())