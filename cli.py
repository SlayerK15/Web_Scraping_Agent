#!/usr/bin/env python
"""
AI Web Scraping Agent - Command Line Interface
This module provides a command-line interface for the web scraping agent.
"""

import os
import sys
import json
import argparse
import logging
from datetime import datetime
from typing import Dict, List, Optional

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler("cli.log"), logging.StreamHandler()]
)
logger = logging.getLogger("WebScraperCLI")

# Import the agent
from agent import WebScraperAgent

def create_job_command(args):
    """Create a new scraping job"""
    agent = WebScraperAgent(config_path=args.config)
    
    # Load selectors from file
    try:
        with open(args.selector_file, 'r') as f:
            selectors = json.load(f)
    except Exception as e:
        logger.error(f"Error loading selector file: {e}")
        sys.exit(1)
    
    # Create job
    job_id = agent.create_scraping_job(
        url=args.url,
        selectors=selectors,
        job_name=args.name
    )
    
    print(f"Created job {job_id}")
    return job_id

def execute_job_command(args):
    """Execute an existing scraping job"""
    agent = WebScraperAgent(config_path=args.config)
    
    success = agent.execute_job(args.job_id)
    
    if success:
        print(f"Job {args.job_id} executed successfully")
    else:
        print(f"Job {args.job_id} failed")
        sys.exit(1)

def status_command(args):
    """Get the status of a job"""
    agent = WebScraperAgent(config_path=args.config)
    
    status = agent.get_job_status(args.job_id)
    
    print(json.dumps(status, indent=2))

def list_jobs_command(args):
    """List all jobs"""
    agent = WebScraperAgent(config_path=args.config)
    
    jobs = agent.list_jobs()
    
    if not jobs:
        print("No jobs found")
    else:
        # Print job information in a table format
        print(f"{'JOB ID':<10} {'NAME':<20} {'STATUS':<12} {'CREATED':<20} {'ITEMS':<10}")
        print(f"{'-'*10} {'-'*20} {'-'*12} {'-'*20} {'-'*10}")
        
        for job in jobs:
            job_id = job.get('job_id', 'N/A')
            job_name = job.get('job_name', 'Unnamed')[:20]
            status = job.get('status', 'unknown')
            created = job.get('created_at', 'N/A')
            items = job.get('items_count', 'N/A')
            
            # Format created date for display
            if created != 'N/A':
                try:
                    created_dt = datetime.fromisoformat(created)
                    created = created_dt.strftime('%Y-%m-%d %H:%M')
                except:
                    pass
            
            print(f"{job_id:<10} {job_name:<20} {status:<12} {created:<20} {items:<10}")

def run_command(args):
    """Run a full scraping job (create and execute in one command)"""
    # Create job
    job_id = create_job_command(args)
    
    # Execute job
    args.job_id = job_id
    execute_job_command(args)

def main():
    """Main CLI function"""
    parser = argparse.ArgumentParser(description="AI Web Scraper Agent CLI")
    parser.add_argument("--config", type=str, help="Path to configuration file")
    
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # Create job command
    create_parser = subparsers.add_parser("create", help="Create a new scraping job")
    create_parser.add_argument("--url", type=str, required=True, help="URL to scrape")
    create_parser.add_argument("--selector-file", type=str, required=True, help="Path to selector file")
    create_parser.add_argument("--name", type=str, help="Job name")
    create_parser.set_defaults(func=create_job_command)
    
    # Execute job command
    execute_parser = subparsers.add_parser("execute", help="Execute a scraping job")
    execute_parser.add_argument("--job-id", type=str, required=True, help="Job ID to execute")
    execute_parser.set_defaults(func=execute_job_command)
    
    # Status command
    status_parser = subparsers.add_parser("status", help="Get job status")
    status_parser.add_argument("--job-id", type=str, required=True, help="Job ID to check")
    status_parser.set_defaults(func=status_command)
    
    # List jobs command
    list_parser = subparsers.add_parser("list", help="List all jobs")
    list_parser.set_defaults(func=list_jobs_command)
    
    # Run command (create and execute)
    run_parser = subparsers.add_parser("run", help="Create and execute a job")
    run_parser.add_argument("--url", type=str, required=True, help="URL to scrape")
    run_parser.add_argument("--selector-file", type=str, required=True, help="Path to selector file")
    run_parser.add_argument("--name", type=str, help="Job name")
    run_parser.set_defaults(func=run_command)
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    # Execute the function for the selected command
    args.func(args)

if __name__ == "__main__":
    main()