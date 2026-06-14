import time
import os
import faultsnap
from faultsnap.core import build_crash_data
from faultsnap.capsule import write_capsule

def benchmark():
    print("FaultSnap Benchmark Suite\n" + "="*25)
    
    # 1. Create a massive object graph
    print("1. Generating massive state...")
    start = time.time()
    
    huge_dict = {}
    for i in range(1000):
        huge_dict[f"key_{i}"] = list(range(100))
        
    huge_list = [huge_dict] * 10
    
    # Nested crash context
    def crash_trigger(data):
        1 / 0
        
    try:
        crash_trigger(huge_list)
    except Exception as e:
        import sys
        exc_type, exc_value, exc_traceback = sys.exc_info()
        
    print(f"   Done in {(time.time() - start)*1000:.2f} ms")
    
    # 2. Benchmark Serialization (build_crash_data)
    print("\n2. Benchmarking Serialization (includes masking and summaries)...")
    start = time.time()
    crash_data = build_crash_data(exc_type, exc_value, exc_traceback)
    serialize_time = (time.time() - start) * 1000
    print(f"   Serialization took: {serialize_time:.2f} ms")
    
    # 3. Benchmark Capsule Creation
    print("\n3. Benchmarking Capsule ZIP I/O...")
    start = time.time()
    capsule_path = write_capsule(crash_data, output_dir=".", prefix="benchmark_")
    io_time = (time.time() - start) * 1000
    print(f"   Capsule I/O took: {io_time:.2f} ms")
    
    # 4. Results
    size_bytes = os.path.getsize(capsule_path)
    print(f"\nResults:")
    print(f"- Total Overhead: {serialize_time + io_time:.2f} ms")
    print(f"- Capsule Size: {size_bytes / 1024:.2f} KB")
    
    os.remove(capsule_path)

if __name__ == "__main__":
    benchmark()
