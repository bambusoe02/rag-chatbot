#!/usr/bin/env python3
"""
Analyze load test results and generate insights
"""

import pandas as pd
import glob
import sys
from pathlib import Path


def analyze_results(report_dir="tests/load/reports"):
    """Analyze load test results from CSV files"""
    
    print("📊 Analyzing Load Test Results\n")
    
    # Find latest test results
    csv_files = glob.glob(f"{report_dir}/*_stats.csv")
    
    if not csv_files:
        print("❌ No test results found")
        return
    
    # Get most recent
    latest_file = max(csv_files, key=lambda x: Path(x).stat().st_mtime)
    
    print(f"📁 Reading: {latest_file}\n")
    
    # Load data
    df = pd.read_csv(latest_file)
    
    # Overall statistics
    print("=" * 60)
    print("OVERALL STATISTICS")
    print("=" * 60)
    
    total_requests = df['Request Count'].sum()
    total_failures = df['Failure Count'].sum()
    failure_rate = (total_failures / total_requests * 100) if total_requests > 0 else 0
    
    print(f"Total Requests:     {total_requests:,}")
    print(f"Total Failures:     {total_failures:,}")
    print(f"Failure Rate:       {failure_rate:.2f}%")
    print(f"Total RPS:          {df['Requests/s'].sum():.2f}")
    print()
    
    # Response time statistics
    print("=" * 60)
    print("RESPONSE TIME STATISTICS (ms)")
    print("=" * 60)
    
    avg_response = df['Average Response Time'].mean()
    min_response = df['Min Response Time'].min()
    max_response = df['Max Response Time'].max()
    median_response = df['Median Response Time'].median()
    
    print(f"Average:            {avg_response:.2f}ms")
    print(f"Median:             {median_response:.2f}ms")
    print(f"Min:                {min_response:.2f}ms")
    print(f"Max:                {max_response:.2f}ms")
    print()
    
    # Percentiles
    if '95%' in df.columns:
        print("PERCENTILES:")
        print(f"  50th (Median):    {df['50%'].median():.2f}ms")
        print(f"  95th:             {df['95%'].median():.2f}ms")
        print(f"  99th:             {df['99%'].median():.2f}ms")
        print()
    
    # Endpoint breakdown
    print("=" * 60)
    print("ENDPOINT BREAKDOWN")
    print("=" * 60)
    
    endpoint_stats = df[df['Name'] != 'Aggregated'].sort_values('Average Response Time', ascending=False)
    
    for _, row in endpoint_stats.iterrows():
        print(f"\n{row['Name']}")
        print(f"  Requests:         {row['Request Count']:,}")
        print(f"  Failures:         {row['Failure Count']:,}")
        print(f"  Avg Response:     {row['Average Response Time']:.2f}ms")
        print(f"  RPS:              {row['Requests/s']:.2f}")
    
    print()
    
    # Performance verdict
    print("=" * 60)
    print("PERFORMANCE VERDICT")
    print("=" * 60)
    
    if failure_rate > 5:
        print("❌ FAILED - High failure rate (>5%)")
    elif avg_response > 3000:
        print("⚠️  WARNING - Slow average response time (>3s)")
    elif avg_response > 1000:
        print("⚠️  OK - Response times acceptable but could be improved")
    else:
        print("✅ PASSED - Good performance!")
    
    print()
    
    # Recommendations
    print("=" * 60)
    print("RECOMMENDATIONS")
    print("=" * 60)
    
    if avg_response > 2000:
        print("• Consider adding caching for frequently accessed data")
        print("• Optimize database queries")
        print("• Scale horizontally (add more instances)")
    
    if failure_rate > 1:
        print("• Investigate error logs for failure causes")
        print("• Add rate limiting protection")
        print("• Increase resource limits")
    
    if df['Requests/s'].sum() < 100:
        print("• System can handle higher load")
        print("• Consider running stress tests")
    
    print()


if __name__ == "__main__":
    report_dir = sys.argv[1] if len(sys.argv) > 1 else "tests/load/reports"
    analyze_results(report_dir)

