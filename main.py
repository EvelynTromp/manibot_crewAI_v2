import asyncio
import argparse
from crews.market_crew import MarketCrew
from utils.logger import get_logger
from config.settings import settings
from pathlib import Path

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
            print("\n🔍 Scanning markets for opportunities...\n")
            results = await crew.scan_markets()
            
            # Calculate success metrics
            successful = len([r for r in results if r.get('success')])
            total = len(results)
            trades = len([r for r in results if r.get('trade_executed')])
            
            # Save reports
            report_path = crew.finalize_scan_session()
            
            # Display results
            print(f"\n✅ Scan complete: Analyzed {total} markets ({successful} successful).")
            if trades > 0:
                print(f"📈 Executed {trades} trades")
            if report_path:
                print(f"📝 Report saved to: {report_path}")
            print()
            
        elif args.market:
            print(f"\n📊 Analyzing market: {args.market}\n")
            result = await crew.analyze_and_trade(args.market)
            
            # Save individual market report
            report_path = crew.finalize_scan_session()
            
            print("\n✅ Analysis complete")
            if report_path:
                print(f"📝 Report saved to: {report_path}")
            print()
            
        elif args.monitor:
            print("\n👀 Monitoring active positions...\n")
            positions = await crew.monitor_positions()
            print(f"\nCurrent positions: {positions}\n")
            
        else:
            print("\n❌ Error: No action specified. Use --scan, --market, or --monitor\n")
            
    except Exception as e:
        logger.error(f"Error in main execution: {str(e)}")
        print(f"\n❌ Error: {str(e)}\n")
        raise

if __name__ == "__main__":
    asyncio.run(main())