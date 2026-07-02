import os
import subprocess

def postprocess(file_path: str):
    """
    Main post-processor method.
    Optimizes the compiled Dafny Rust code by running the compiled Rust postprocessor.
    """
    if not os.path.exists(file_path):
        return

    # Find the postprocessor binary
    current_dir = os.path.dirname(os.path.abspath(__file__))
    binary_path = os.path.join(current_dir, "postprocessor-rust", "target", "release", "postprocessor_rust")

    # If the binary doesn't exist, compile it first
    if not os.path.exists(binary_path):
        print("Compiling Rust postprocessor...")
        manifest_path = os.path.join(current_dir, "postprocessor-rust", "Cargo.toml")
        res = subprocess.run(
            ["cargo", "build", "--release", "--manifest-path", manifest_path],
            capture_output=True,
            text=True
        )
        if res.returncode != 0:
            raise RuntimeError(f"Failed to compile Rust postprocessor:\n{res.stderr}")

    # Run the postprocessor binary on the file
    res = subprocess.run([binary_path, file_path, "ssb-dbgen/lineorder_flat.tbl"], capture_output=True, text=True)
    if res.stderr:
        import sys
        sys.stderr.write(res.stderr)
    if res.returncode != 0:
        raise RuntimeError(f"Rust postprocessor failed on {file_path}:\n{res.stderr}")
