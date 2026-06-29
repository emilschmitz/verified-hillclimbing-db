import os
import json
import subprocess

def reprocess_all():
    print("=== Reprocessing Q1-Q5 Experiments with OnceLock Column Projection ===")
    
    results = {}
    
    for q in range(1, 6):
        history_path = f"experiments/Q{q}/history.json"
        if not os.path.exists(history_path):
            print(f"Query {q}: No history found.")
            continue
            
        with open(history_path, "r") as f:
            history = json.load(f)
            
        # Find the last successful record with code
        last_success = None
        for record in reversed(history):
            if record["status"] == "SUCCESS" and record.get("code"):
                last_success = record
                break
                
        if not last_success:
            print(f"Query {q}: No successful iteration found in history.")
            continue
            
        print(f"\n--- Reprocessing Query {q} (from Iteration {last_success['iteration']}) ---")
        
        # Write the code to scratchpad
        scratchpad_path = "research_loop/agent_scratchpad.md"
        with open(scratchpad_path, "w") as f:
            f.write(f"```dafny\n{last_success['code']}\n```")
            
        # Run harness
        harness_cmd = [
            "uv", "run", "python", "research_loop/harness.py",
            "-q", str(q),
            "--dataset-size", "50000"
        ]
        
        harness_res = subprocess.run(harness_cmd, capture_output=True, text=True)
        
        try:
            metrics = json.loads(harness_res.stdout)
        except json.JSONDecodeError:
            metrics = {
                "status": "FAILURE",
                "latency_us": -1,
                "compiler_error": f"Harness crashed: {harness_res.stderr}"
            }
            
        print(f"Result: {metrics['status']}, Latency: {metrics['latency_us']} us")
        
        if metrics["status"] == "SUCCESS":
            results[q] = metrics["latency_us"]
            
            # Add a new iteration to the history reflecting the post-processed result
            new_record = last_success.copy()
            new_record["iteration"] = len(history) + 1
            new_record["rust_latency_us"] = metrics["latency_us"]
            new_record["compiler_error"] = ""
            new_record["verification_time_ms"] = metrics.get("verification_time_ms", -1)
            new_record["compilation_time_ms"] = metrics.get("compilation_time_ms", -1)
            new_record["agent_time_ms"] = 0 # No LLM call!
            new_record["cost_usd"] = 0.0 # Free!
            new_record["cumulative_cost_usd"] = history[-1]["cumulative_cost_usd"]
            
            history.append(new_record)
            with open(history_path, "w") as f:
                json.dump(history, f, indent=2)
                
            # Regenerate plots
            from run_experiments import run_duckdb_baseline, generate_plots
            duckdb_lat = run_duckdb_baseline(q, 50000)
            generate_plots(q, history_path, duckdb_lat, f"experiments/Q{q}")
        else:
            print(f"Error: {metrics['compiler_error']}")

    print("\n=== Reprocessing Complete ===")
    for q, lat in results.items():
        print(f"Query {q}: {lat} us")

if __name__ == "__main__":
    reprocess_all()
