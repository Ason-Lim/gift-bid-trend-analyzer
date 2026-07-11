#!/usr/bin/env python3
import os
import sys
from crawler.core_crawler import run_crawler_generator

def main():
    print("==================================================")
    print("Starting B2B Gift Bid Batch Crawler...")
    print("==================================================")
    
    # We want to run the B2B Gift Bid crawler
    # Core crawler generator yields SSE logs like: 'data: [INFO] ...\n\n'
    generator = run_crawler_generator(tab='b2b_gift', simulate=True)
    
    for message in generator:
        clean_msg = message.strip()
        if clean_msg.startswith("data:"):
            clean_msg = clean_msg.replace("data:", "", 1).strip()
        if clean_msg:
            print(clean_msg)
            
    print("==================================================")
    print("Batch Crawler Execution Completed.")
    print("==================================================")

if __name__ == '__main__':
    main()
