import os
import time
import json
import threading
import random
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(filename="app.log", level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Sample API simulation function
def simulated_api_request(data):
    time.sleep(random.uniform(0.5, 2.0))  # Simulate API delay
    response = {"status": "success", "received_data": data, "processed_at": datetime.now().isoformat()}
    logging.info(f"API Response: {response}")
    return response

# Generate and process sample data
def generate_sample_data(file_path):
    sample_data = [{"id": i, "value": random.randint(10, 100)} for i in range(1, 101)]
    
    with open(file_path, "w") as f:
        json.dump(sample_data, f, indent=4)

    logging.info(f"Sample data written to {file_path}")

def process_sample_data(file_path):
    if not os.path.exists(file_path):
        logging.error(f"File {file_path} not found!")
        return
    
    with open(file_path, "r") as f:
        data = json.load(f)

    processed_data = [{"id": item["id"], "square": item["value"]**2, "cube": item["value"]**3} for item in data]
    
    output_file = "processed_data.json"
    with open(output_file, "w") as f:
        json.dump(processed_data, f, indent=4)

    logging.info(f"Processed data written to {output_file}")

# Perform complex calculations
def perform_calculations():
    results = {}
    for i in range(1, 100001):
        results[i] = i ** 0.5 + i ** 1.5 - i ** 2
    logging.info("Complex calculations completed.")

# Simulated multi-threaded API calls
def run_api_tests():
    threads = []
    for i in range(5):
        thread = threading.Thread(target=simulated_api_request, args=({"test_id": i},))
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()

    logging.info("All API tests completed.")

# Main execution flow
if __name__ == "__main__":
    logging.info("Script started.")
    
    file_path = "sample_data.json"
    generate_sample_data(file_path)
    
    time.sleep(1)  # Simulate delay
    
    process_sample_data(file_path)

    # Run API tests in background
    api_thread = threading.Thread(target=run_api_tests)
    api_thread.start()

    # Perform calculations in another thread
    calc_thread = threading.Thread(target=perform_calculations)
    calc_thread.start()

    # Wait for both threads to finish
    api_thread.join()
    calc_thread.join()

    logging.info("All tasks completed successfully.")
    print("All tasks completed! Check logs and output files.")
