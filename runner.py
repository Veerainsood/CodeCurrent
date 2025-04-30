#!/usr/bin/env python3
import subprocess
import os
import sys
import shutil
import time
from pathlib import Path

base_dir =  Path(os.getcwd())

def ensure_docker_installed():
    """
    Ensures that Docker is installed on the system. If not installed, 
    attempts to install Docker based on the operating system (Linux, macOS, or Windows).
    """
    if shutil.which("docker") is None:
        print("Docker is not installed.")

        # Try to install based on OS — placeholder logic
        if sys.platform.startswith("linux"):
            print("Attempting to install Docker for Linux (requires sudo)...")
            try:
                subprocess.check_call([
                    "sudo", "apt-get", "update" 
                ])
                subprocess.check_call([
                    "sudo", "apt-get", "install", "-y", "docker.io"
                ])
                subprocess.check_call([
                    "sudo", "systemctl", "start", "docker"
                ])
                subprocess.check_call([
                    "sudo", "systemctl", "enable", "docker"
                ])
                print("Docker installed successfully.")
            except subprocess.CalledProcessError as e:
                print("Failed to install Docker:", e)
                sys.exit(1)

        elif sys.platform == "darwin":
            print("Please install Docker Desktop from https://www.docker.com/products/docker-desktop")
            sys.exit(1)

        elif sys.platform == "win32":
            print("Please install Docker Desktop from https://www.docker.com/products/docker-desktop")
            sys.exit(1)

        else:
            print("Unsupported platform.")
            sys.exit(1)

    else:
        print("Docker is already installed.")

def is_container_running(name):
    """
    Checks if a Docker container with the given name is currently running.

    Args:
    - name: The name of the container to check.

    Returns:
    - True if the container is running, False otherwise.
    """
    try:
        output = subprocess.check_output(
            ["docker", "ps", "--filter", f"name={name}", "--format", "{{.Names}}"],
            universal_newlines=True,
        )
        return output.strip() == name
    except subprocess.CalledProcessError:
        return False

def container_exists(name):
    """
    Checks if a Docker container with the given name exists (whether running or stopped).

    Args:
    - name: The name of the container to check.

    Returns:
    - True if the container exists, False otherwise.
    """
    try:
        output = subprocess.check_output(
            ["docker", "ps", "-a", "--filter", f"name={name}", "--format", "{{.Names}}"],
            universal_newlines=True,
        )
        return output.strip() == name
    except subprocess.SubprocessError:
        return False

def remove_existing_container(name):
    """
    Removes an existing Docker container with the given name, if it exists.

    Args:
    - name: The name of the container to remove.
    """
    try:
        print("Came Here")
        subprocess.check_call(["docker", "rm", "-f", name])
        print(f"Removed existing container: {name}")
    except subprocess.SubprocessError as e:
        print("Error removing existing container:", e)
        # sys.exit(1)


def start_container(container_name, image_name):
    """
    Starts a Docker container with the given name and image.

    If the container already exists, it will be removed and restarted.

    Args:
    - container_name: The name of the container to start.
    - image_name: The image to use for starting the container.
    """
    global base_dir
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
    except subprocess.SubprocessError:
        print(f"Image '{image_name}' not found locally. Pulling...")
        subprocess.check_call(["docker", "pull", image_name])
        print("Retrying container start...")
        subprocess.check_call(cmd)
        print(f"Started container: {container_name}")
        time.sleep(2)

def run_generator_in_container(container_name, mode):
    """
    Runs a script inside the container based on the specified mode.

    Args:
    - container_name: The name of the container in which to run the script.
    - mode: The mode determines which script to run (0 = C++, 1 = Java, 2 = interlang C++).
    """
    # mode: 0 = cpp, 1 = java, 2 = interlangcpp
    docker_cmd =[]
    docker_cmd2 =[]
    if mode == 0:
        bash_file = "./runner_cpp.sh"
        bash_file2 = "./runner_java.sh"
        docker_cmd = ["docker", "exec", container_name, "bash", "-c", bash_file]
        docker_cmd2 = ["docker", "exec", container_name, "bash", "-c", bash_file2]
    elif mode == 2:
        bash_file = "./runner_interlangcpp.sh"
        docker_cmd = ["docker", "exec", container_name, "bash", "-c", bash_file]
    else:
        raise ValueError("Unknown mode for generator script")

    try:
        subprocess.check_call(docker_cmd)
        if mode == 0:
            subprocess.check_call(docker_cmd2)
            pass
        print(f"Generator command ({bash_file}) executed successfully in container: {container_name}")
    except subprocess.CalledProcessError as e:
        print("Error executing generator command:", e)
        sys.exit(1)


def stop_and_remove_container(container_name):
    """
    Stops and removes a Docker container with the given name.

    Args:
    - container_name: The name of the container to stop and remove.
    """
    try:
        subprocess.check_call(["docker", "stop", container_name])
        subprocess.check_call(["docker", "rm", container_name])
        print(f"Container {container_name} stopped and removed.")
    except subprocess.CalledProcessError as e:
        print("Error stopping/removing container:", e)

def main(container_name, image_name, mode):
    """
    Main function to ensure Docker is installed, start the container if it's not running,
    run the appropriate generator script inside the container, and then stop and remove the container.

    Args:
    - container_name: The name of the container.
    - image_name: The Docker image to use for the container.
    - mode: Mode specifying which generator script to run (0, 1, or 2).
    """
    if not is_container_running(container_name):
        print(f"Container {container_name} not running. Starting container...")
        start_container(container_name, image_name)
    else:
        print(f"Container {container_name} is already running.")

    run_generator_in_container(container_name=container_name, mode=mode)
    stop_and_remove_container(container_name=container_name)

# Run the three containers
ensure_docker_installed()

main("cpp_parser_container", "veerain/cplusplusparser:latest", 0)
# Final steps
os.system("python3 pythonMaker.py")
os.system("python3 combineJsons.py")

main("cpp_parser_container", "veerain/cplusplusparser:latest", 2)

import json

def load_json(path):
    """
    Loads a JSON file from the given path.

    Args:
    - path: The path to the JSON file.

    Returns:
    - The loaded JSON data.
    """
    with open(path, 'r') as f:
        return json.load(f)

def save_json(data, path):
    """
    Saves the provided data to a JSON file at the specified path.

    Args:
    - data: The data to save.
    - path: The path where the JSON file will be saved.
    """
    with open(path, 'w') as f:
        json.dump(data, f, indent=4)

# Load the caller-callee pairs JSON file.
caller_callee_pairs = load_json("interlangCpp.json")
    
# Load the function_calls_combined JSON file.
function_calls_combined = load_json("function_calls_combined.json")

# Concatenate the two lists.
combined = caller_callee_pairs + function_calls_combined
    
# Save the combined list to a new file.
save_json(combined, "function_calls_combined.json")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def fix_path(path):
    """
    Fixes the path to ensure it points correctly based on the current directory structure.

    Args:
    - path: The path to fix.

    Returns:
    - The corrected path.
    """
    if isinstance(path, str) and path.startswith("/src"):
        return os.path.join(BASE_DIR, path[len("/src"):].lstrip("/"))
    return path

def fix_paths_in_json(obj):
    """
    Recursively fixes the paths in a JSON object by applying the fix_path function.

    Args:
    - obj: The JSON object to fix.

    Returns:
    - The updated JSON object with fixed paths.
    """
    if isinstance(obj, dict):
        return {k: fix_path(v) if k == "path" else fix_paths_in_json(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [fix_paths_in_json(item) for item in obj]
    else:
        return obj

with open("unique_functions_combined.json", "r", encoding="utf-8") as f:
    data2 = json.load(f)

fixed_data2 = fix_paths_in_json(data2)

with open("unique_functions_combined.json", "w", encoding="utf-8") as f:
    json.dump(fixed_data2, f, indent=2)

print(f"Combined JSON written with {len(combined)} entries.")
