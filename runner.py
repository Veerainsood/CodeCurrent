#!/usr/bin/env python3
import subprocess
import os
import sys
import time
from pathlib import Path

# Configuration
base_dir = Path(os.getcwd())

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

def start_container(container_name,image_name):
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

def run_generator_in_container(container_name,javPy):
    if(javPy == 0):
        docker_cmd = ["docker", "exec", container_name, "bash", "-c", "./tester.sh"]
    else:
        docker_cmd = ["docker", "exec", container_name, "bash", "-c", "./tester_java.sh"]
    try:
        subprocess.check_call(docker_cmd)
        print("Generator command executed successfully in container.")
    except subprocess.CalledProcessError as e:
        print("Error executing generator command:", e)
        sys.exit(1)

def stop_and_remove_container(container_name):
    try:
        subprocess.check_call(["docker", "stop", container_name])
        subprocess.check_call(["docker", "rm", container_name])
        print(f"Container {container_name} stopped and removed.")
    except subprocess.CalledProcessError as e:
        print("Error stopping/removing container:", e)

def main(container_name,image_name):
    if not is_container_running(container_name):
        print("Container not running. Starting container...")
        start_container(container_name,image_name)
    else:
        print("Container is already running.")

    print("Running generator on all C++ files...")
    if(container_name == "cpp_parser_container"):
        run_generator_in_container(container_name=container_name,javPy=0)
    else:
        run_generator_in_container(container_name=container_name,javPy=1)
    stop_and_remove_container(container_name=container_name)


container_name = "cpp_parser_container"
image_name = "veerain/cplusplusparser:latest"
main(container_name,image_name)
container_name = "java_parser_container"
image_name = "veerain/cplusplusparser:javaInterlang"
main(container_name,image_name)
os.system("python3 pythonMaker.py")
os.system("python3 combineJsons.py")

