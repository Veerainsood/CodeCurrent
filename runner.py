#!/usr/bin/env python3
import subprocess
import os
import sys
import time
from pathlib import Path

# Configuration
container_name = "cpp_parser_container"
image_name = "veerain/cplusplusparser:latest"
base_dir = Path(os.getcwd())
final_json = base_dir / "file.json"

def is_container_running(name):
    try:
        output = subprocess.check_output(
            ["docker", "ps", "--filter", f"name={name}", "--format", "{{.Names}}"],
            universal_newlines=True,
        )
        return output.strip() == name
    except subprocess.CalledProcessError:
        return False

def container_exists(name):
    try:
        output = subprocess.check_output(
            ["docker", "ps", "-a", "--filter", f"name={name}", "--format", "{{.Names}}"],
            universal_newlines=True,
        )
        return output.strip() == name
    except subprocess.CalledProcessError:
        return False

def remove_existing_container(name):
    try:
        subprocess.check_call(["docker", "rm", "-f", name])
        print(f"Removed existing container: {name}")
    except subprocess.CalledProcessError as e:
        print("Error removing existing container:", e)
        sys.exit(1)

def start_container():
    if container_exists(container_name):
        remove_existing_container(container_name)

    cmd = [
        "docker", "run", "-dit", "--name", container_name,
        "--mount", f"type=bind,src={base_dir},dst=/src",
        image_name,
        "bash"
    ]
    try:
        subprocess.check_call(cmd)
        print(f"Started container: {container_name}")
        time.sleep(2)  # Let container settle
    except subprocess.CalledProcessError as e:
        print("Error starting container:", e)
        sys.exit(1)

def run_generator_in_container():
    docker_cmd = ["docker", "exec", container_name, "bash", "-c", "./tester.sh"]
    try:
        subprocess.check_call(docker_cmd)
        print("Generator command executed successfully in container.")
    except subprocess.CalledProcessError as e:
        print("Error executing generator command:", e)
        sys.exit(1)

def copy_json_to_current():
    src = base_dir / "file.json"
    if src.exists():
        print(f"Output file generated at: {src}")
    else:
        print("file.json not found. Make sure tester.sh writes to /src/file.json")

def stop_and_remove_container():
    try:
        subprocess.check_call(["docker", "stop", container_name])
        subprocess.check_call(["docker", "rm", container_name])
        print(f"Container {container_name} stopped and removed.")
    except subprocess.CalledProcessError as e:
        print("Error stopping/removing container:", e)

def main():
    if not is_container_running(container_name):
        print("Container not running. Starting container...")
        start_container()
    else:
        print("Container is already running.")

    print("Running generator on all C++ files...")
    run_generator_in_container()
    copy_json_to_current()
    stop_and_remove_container()

if __name__ == "__main__":
    main()
