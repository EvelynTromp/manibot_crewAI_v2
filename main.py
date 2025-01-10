import asyncio
import argparse
import logging
from market_trader import MarketTrader
from utils.logger import get_logger

logger = get_logger(__name__)

async def main():
    parser = argparse.ArgumentParser(description='ManifoldBot - Autonomous Trading Bot')
    parser.add_argument('--scan', action='store_true', help='Scan markets for opportunities')
    parser.add_argument('--market', type=str, help='Analyze specific market ID')
    parser.add_argument('--monitor', action='store_true', help='Monitor active positions')
    parser.add_argument('--verbose', '-v', action='store_true', help='Enable debug logging')
    args = parser.parse_args()

    # Set debug logging if verbose flag is used
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
        logging.getLogger('market_analyzer').setLevel(logging.DEBUG)

    logger.info("Starting bot...")
    trader = MarketTrader()
    
    try:
        if args.scan:
            print("\n🔍 Scanning markets for opportunities...\n")
            results = await trader.scan_markets()
            successful = len([r for r in results if r.get('success')])
            trades = len([r for r in results if r.get('trade_executed')])
            print(f"\n✅ Scan complete: Analyzed {len(results)} markets ({successful} successful)")
            if trades > 0:
                print(f"📈 Executed {trades} trades")
            print()
            
        elif args.market:
            print(f"\n📊 Analyzing market: {args.market}\n")
            result = await trader.analyze_and_trade(args.market)
            print("\n✅ Analysis complete")
            if result.get('trade_executed'):
                print("📈 Trade executed successfully")
            print()
            
        elif args.monitor:
            print("\n👀 Monitoring active positions...\n")
            positions = await trader.monitor_positions()
            for pos in positions:
                print(f"Market {pos['market_id']}: {'Resolved' if pos['is_resolved'] else 'Active'}")
                print(f"P&L: ${pos['profit_loss']:.2f}")
            print()
            
        else:
            print("\n❌ Error: No action specified. Use --scan, --market, or --monitor\n")
            
    except Exception as e:
        logger.error(f"Error in main execution: {str(e)}")
        print(f"\n❌ Error: {str(e)}\n")
        raise

if __name__ == "__main__":
    asyncio.run(main())