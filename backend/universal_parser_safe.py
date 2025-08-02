"""Safe wrapper for universal parser with timeout protection"""

import multiprocessing
import time
from universal_parser import parse_universal_pdf as original_parser

def parse_universal_pdf_with_timeout(pdf_path, timeout=45):
    """
    Parse PDF with timeout protection using multiprocessing.
    Falls back to empty list if timeout occurs.
    """
    def worker(pdf_path, result_queue):
        try:
            result = original_parser(pdf_path)
            result_queue.put(result)
        except Exception as e:
            print(f"Parser error: {e}")
            result_queue.put([])
    
    # Create a queue to get results
    result_queue = multiprocessing.Queue()
    
    # Create and start the process
    process = multiprocessing.Process(target=worker, args=(pdf_path, result_queue))
    process.start()
    
    # Wait for the process to complete or timeout
    process.join(timeout=timeout)
    
    if process.is_alive():
        # Timeout occurred
        print(f"Parser timed out after {timeout} seconds")
        process.terminate()
        process.join()
        return []
    
    # Get the result
    try:
        return result_queue.get_nowait()
    except:
        return []

# Export as the main function
parse_universal_pdf = parse_universal_pdf_with_timeout