"""
Options Trading - End of Day Report
Analyzes what went well and what went wrong
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from datetime import date, timedelta
from services.analytics.options_analytics import OptionsAnalytics


def main():
    analytics = OptionsAnalytics()
    
    print("\n" + "=" * 80)
    print("OPTIONS TRADING - END OF DAY REPORT GENERATOR")
    print("=" * 80)
    
    # Generate today's report
    print("\n📅 Generating report for today...")
    report = analytics.generate_eod_report()
    
    if report:
        analytics.print_eod_report(report)
        analytics.save_eod_report(report)
        
        print("💾 Report saved to database (options_daily_analytics table)")
    else:
        print("\n⚠️  No trading activity today")
        
        # Check yesterday
        print("\n📅 Checking yesterday's report...")
        yesterday = date.today() - timedelta(days=1)
        report_yesterday = analytics.generate_eod_report(yesterday)
        
        if report_yesterday:
            analytics.print_eod_report(report_yesterday)
        else:
            print("No trading activity yesterday either")
    
    print("\n" + "=" * 80 + "\n")


if __name__ == "__main__":
    main()
