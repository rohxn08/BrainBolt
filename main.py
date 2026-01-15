import logging
import argparse
import sys
from src.pipeline import BrainBoltPipeline
from dotenv import load_dotenv

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

def main():
   
    load_dotenv()
    
    parser = argparse.ArgumentParser(description="BrainBolt CLI")
    parser.add_argument("source", help="Path to image, file, or YouTube URL")
    parser.add_argument("--task", default="summarize", choices=["summarize"], help="Task to perform")
    parser.add_argument("--type", default="concise", help="Summary type (concise, educational, etc.)")
    
    args = parser.parse_args()
    
    print(f"BrainBolt Processing: {args.source}")
    
    pipeline = BrainBoltPipeline()
    
    result = pipeline.process(args.source, task=args.task, summary_type=args.type)
    
    if "error" in result:
        print(f"Error: {result['error']}")
    else:
        print("\n" + "="*50)
        print(f"Result ({args.type}):\n")
        print(result['result'])
        print("="*50)

if __name__ == "__main__":
    main()