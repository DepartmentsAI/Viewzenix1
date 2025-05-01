#!/usr/bin/env python3
"""
Daily Test Status Report Generator

This script generates a daily test status report based on test results
collected during the final testing phase. It creates a markdown report
using the template in docs/testing/templates/DAILY_TEST_STATUS_REPORT.md.
"""

import os
import sys
import json
import datetime
import argparse
from typing import Dict, List, Any

# Configuration
DEFAULT_TEMPLATE_PATH = "../../docs/testing/templates/DAILY_TEST_STATUS_REPORT.md"
DEFAULT_OUTPUT_DIR = "../../docs/testing/reports"
DEFAULT_RESULTS_DIR = "./results"

def load_test_results(results_dir: str) -> Dict[str, Any]:
    """
    Load test results from JSON files in the results directory.
    Each file should contain results for a specific component or test type.
    
    Args:
        results_dir: Directory containing test result JSON files
        
    Returns:
        Dictionary of combined test results
    """
    results = {
        "webhook_system": {"planned": 0, "executed": 0, "passed": 0, "notes": ""},
        "order_execution": {"planned": 0, "executed": 0, "passed": 0, "notes": ""},
        "risk_management": {"planned": 0, "executed": 0, "passed": 0, "notes": ""},
        "dashboard_ui": {"planned": 0, "executed": 0, "passed": 0, "notes": ""},
        "performance_tests": {"planned": 0, "executed": 0, "passed": 0, "notes": ""},
        "security_tests": {"planned": 0, "executed": 0, "passed": 0, "notes": ""},
        "issues": []
    }
    
    # Check if results directory exists
    if not os.path.exists(results_dir):
        print(f"Results directory not found: {results_dir}")
        return results
    
    # Load each JSON file in the results directory
    for filename in os.listdir(results_dir):
        if not filename.endswith('.json'):
            continue
            
        filepath = os.path.join(results_dir, filename)
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
                
                # Update component results
                component = filename.split('_results')[0].lower()
                if component in results:
                    results[component]["planned"] += data.get("planned", 0)
                    results[component]["executed"] += data.get("executed", 0)
                    results[component]["passed"] += data.get("passed", 0)
                    results[component]["notes"] = data.get("notes", "")
                
                # Add issues
                if "issues" in data:
                    for issue in data["issues"]:
                        results["issues"].append(issue)
                        
        except Exception as e:
            print(f"Error loading {filepath}: {e}")
    
    return results

def generate_report(template_path: str, results: Dict[str, Any], output_path: str) -> None:
    """
    Generate a markdown report using the template and test results.
    
    Args:
        template_path: Path to the report template
        results: Dictionary of test results
        output_path: Path to save the generated report
    """
    try:
        # Load template
        with open(template_path, 'r') as f:
            template = f.read()
        
        # Replace date placeholder
        today = datetime.datetime.now().strftime("%Y-%m-%d")
        report = template.replace("[Date]", today)
        
        # Calculate totals
        total_planned = sum(comp["planned"] for comp in results.values() if isinstance(comp, dict) and "planned" in comp)
        total_executed = sum(comp["executed"] for comp in results.values() if isinstance(comp, dict) and "executed" in comp)
        total_passed = sum(comp["passed"] for comp in results.values() if isinstance(comp, dict) and "passed" in comp)
        pass_rate = (total_passed / total_executed * 100) if total_executed > 0 else 0
        
        # Create executive summary
        exec_summary = f"""Testing completed {total_executed} of {total_planned} planned test cases ({total_executed/total_planned*100:.1f}% completion). 
Overall pass rate is {pass_rate:.1f}%. {len(results['issues'])} new issues were identified."""
        
        report = report.replace("[Brief summary of today's testing activities, major findings, and current status]", exec_summary)
        
        # Fill in test execution progress table
        report_lines = report.split('\n')
        table_start_idx = None
        
        for i, line in enumerate(report_lines):
            if "| Component | Test Cases Planned | Test Cases Executed | Pass Rate | Notes |" in line:
                table_start_idx = i + 2  # Skip header and separator lines
                break
        
        if table_start_idx:
            # Replace component rows
            for component, data in results.items():
                if not isinstance(data, dict) or component == "issues":
                    continue
                    
                pass_rate = (data["passed"] / data["executed"] * 100) if data["executed"] > 0 else 0
                component_name = component.replace("_", " ").title()
                
                table_row = f"| {component_name} | {data['planned']} | {data['executed']} | {pass_rate:.1f}% | {data['notes']} |"
                
                if table_start_idx < len(report_lines):
                    # Check if this component already has a row in the template
                    component_idx = None
                    for j in range(table_start_idx, len(report_lines)):
                        if report_lines[j].startswith(f"| {component_name} "):
                            component_idx = j
                            break
                    
                    if component_idx:
                        report_lines[component_idx] = table_row
            
            # Set total row
            total_pass_rate = (total_passed / total_executed * 100) if total_executed > 0 else 0
            total_row = f"| **TOTAL** | {total_planned} | {total_executed} | {total_pass_rate:.1f}% | |"
            
            # Find total row
            total_idx = None
            for j in range(table_start_idx, len(report_lines)):
                if "| **TOTAL** |" in report_lines[j]:
                    total_idx = j
                    break
            
            if total_idx:
                report_lines[total_idx] = total_row
        
        # Fill in issues tables
        critical_issues = [issue for issue in results["issues"] if issue.get("severity", "").lower() == "critical"]
        high_issues = [issue for issue in results["issues"] if issue.get("severity", "").lower() == "high"]
        medium_issues = [issue for issue in results["issues"] if issue.get("severity", "").lower() == "medium"]
        low_issues = [issue for issue in results["issues"] if issue.get("severity", "").lower() == "low"]
        
        critical_table = "\n".join(f"| {issue.get('id', '')} | {issue.get('description', '')} | {issue.get('component', '')} | {issue.get('severity', '')} | {issue.get('assignee', '')} | {issue.get('status', '')} |" for issue in critical_issues)
        high_table = "\n".join(f"| {issue.get('id', '')} | {issue.get('description', '')} | {issue.get('component', '')} | {issue.get('severity', '')} | {issue.get('assignee', '')} | {issue.get('status', '')} |" for issue in high_issues)
        med_table = "\n".join(f"| {issue.get('id', '')} | {issue.get('description', '')} | {issue.get('component', '')} | {issue.get('severity', '')} | {issue.get('assignee', '')} | {issue.get('status', '')} |" for issue in medium_issues)
        low_table = "\n".join(f"| {issue.get('id', '')} | {issue.get('description', '')} | {issue.get('component', '')} | {issue.get('severity', '')} | {issue.get('assignee', '')} | {issue.get('status', '')} |" for issue in low_issues)
        
        report = "\n".join(report_lines)
        
        # If no entries, add placeholder
        if not critical_issues:
            critical_table = "| | No critical issues identified | | | | |"
        if not high_issues:
            high_table = "| | No high priority issues identified | | | | |"
        if not medium_issues:
            med_table = "| | No medium priority issues identified | | | | |"
        if not low_issues:
            low_table = "| | No low priority issues identified | | | | |"
        
        # Replace issue tables
        report = report.replace("| | | | | | |", critical_table, 1)
        report = report.replace("| | | | | | |", high_table, 1)
        report = report.replace("| | | | | | |", med_table, 1)
        report = report.replace("| | | | | | |", low_table, 1)
        
        # Save report
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w') as f:
            f.write(report)
            
        print(f"Report generated: {output_path}")
        
    except Exception as e:
        print(f"Error generating report: {e}")

def main():
    parser = argparse.ArgumentParser(description='Generate daily test status report')
    parser.add_argument('--template', type=str, default=DEFAULT_TEMPLATE_PATH,
                        help=f'Path to report template (default: {DEFAULT_TEMPLATE_PATH})')
    parser.add_argument('--results', type=str, default=DEFAULT_RESULTS_DIR,
                        help=f'Directory containing test results (default: {DEFAULT_RESULTS_DIR})')
    parser.add_argument('--output', type=str, 
                        help=f'Output file path (default: {DEFAULT_OUTPUT_DIR}/daily_report_YYYY-MM-DD.md)')
    args = parser.parse_args()
    
    # Set default output path if not provided
    if not args.output:
        today = datetime.datetime.now().strftime("%Y-%m-%d")
        args.output = os.path.join(DEFAULT_OUTPUT_DIR, f"daily_report_{today}.md")
    
    # Load test results
    results = load_test_results(args.results)
    
    # Generate report
    generate_report(args.template, results, args.output)

if __name__ == "__main__":
    main() 