#!/usr/bin/env python3
"""Analyze trading outcomes and get recommendations."""

import sys
import os
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

from ml.trade_learner import learn_from_trading_outcomes, TradeHistoryAnalyzer
import json

def main():
    """Analyze trade history and print recommendations."""
    print("=" * 60)
    print("SolBot Trade Outcome Analysis")
    print("=" * 60)
    print()
    
    recommendations = learn_from_trading_outcomes()
    
    if not recommendations or recommendations.get('total_trades', 0) == 0:
        print("??  No trade history found!")
        print()
        print("To generate trade history:")
        print("  1. Run simulations: python simulate.py")
        print("  2. Or enable live trading: python live_trade.py")
        print("  3. Trades are logged to: trade_log.json")
        print()
        return
    
    print(f"?? Analysis Results:")
    print(f"   Total trades analyzed: {recommendations['total_trades']}")
    print(f"   Profitability rate: {recommendations['profitability_rate']:.2%}")
    print()
    
    if recommendations.get('optimal_confidence_threshold'):
        print(f"? Recommended confidence threshold: {recommendations['optimal_confidence_threshold']:.2f}")
        print(f"   (Current: Check config/config.py)")
        print()
    
    # Show top profitable patterns
    profitable = recommendations.get('profitable_patterns', {})
    if profitable:
        print("?? Top Profitable Patterns:")
        top_profitable = sorted(profitable.items(), key=lambda x: x[1], reverse=True)[:5]
        for pattern, count in top_profitable:
            print(f"   {pattern}: {count} profitable trades")
        print()
    
    # Show patterns to avoid
    unprofitable = recommendations.get('unprofitable_patterns', {})
    if unprofitable:
        print("? Patterns to Avoid:")
        top_unprofitable = sorted(unprofitable.items(), key=lambda x: x[1], reverse=True)[:5]
        for pattern, count in top_unprofitable:
            print(f"   {pattern}: {count} unprofitable trades")
        print()
    
    print("=" * 60)
    print("?? To use these recommendations:")
    print("   1. Review the patterns above")
    print("   2. Adjust config/config.py accordingly")
    print("   3. Consider updating indicator weights")
    print("=" * 60)

if __name__ == '__main__':
    main()
