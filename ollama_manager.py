#!/usr/bin/env python3
"""
Ollama RunPod Manager for WhatIfWeBelieved Agent
Usage: python ollama_manager.py [deploy|start|stop|pull|status|url]
"""

import subprocess
import json
import sys
import time
import requests
from typing import Optional

POD_NAME = "ollama-theology-agent"
GPU_TYPE = "RTX A6000"
IMAGE = "ollama/ollama:latest"
CONTAINER_DISK = 50
PORTS = "11434/http"
OLLAMA_ORIGINS = "https://whatifwebelieved.vercel.app"
DEFAULT_MODEL = "llama3.3:70b-instruct-q4_K_M"

def run_cmd(cmd: list, capture=True) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, capture_output=capture, text=True)

def get_pod_id() -> Optional[str]:
    result = run_cmd(["runpodctl", "get", "pods", "--name", POD_NAME, "--output", "json"])
    if result.returncode == 0:
        pods = json.loads(result.stdout)
        return pods[0]["id"] if pods else None
    return None

def get_pod_status(pod_id: str) -> dict:
    result = run_cmd(["runpodctl", "get", "pod", pod_id, "--output", "json"])
    if result.returncode == 0:
        return json.loads(result.stdout)
    return {}

def get_public_url(pod_id: str) -> Optional[str]:
    pod = get_pod_status(pod_id)
    for port in pod.get("ports", []):
        if port.get("privatePort") == 11434:
            return port.get("publicUrl")
    return None

def deploy():
    """Deploy new Ollama pod"""
    pod_id = get_pod_id()
    if pod_id:
        print(f"Pod already exists: {pod_id}")
        return start()
    
    print(f"Creating pod: {POD_NAME}...")
    cmd = [
        "runpodctl", "create", "pod",
        "--name", POD_NAME,
        "--image", IMAGE,
        "--gpu-type", GPU_TYPE,
        "--gpu-count", "1",
        "--ports", PORTS,
        "--container-disk", str(CONTAINER_DISK),
        "--env", f"OLLAMA_ORIGINS={OLLAMA_ORIGINS}",
        "--env", "OLLAMA_HOST=0.0.0.0:11434",
        "--output", "json"
    ]
    result = run_cmd(cmd)
    if result.returncode != 0:
        print(f"Failed: {result.stderr}")
        return
    
    pod_info = json.loads(result.stdout)
    pod_id = pod_info["id"]
    print(f"Created: {pod_id}")
    start()

def start():
    """Start existing pod"""
    pod_id = get_pod_id()
    if not pod_id:
        print("No pod found. Run deploy first.")
        return
    
    print(f"Starting pod {pod_id}...")
    run_cmd(["runpodctl", "start", "pod", pod_id])
    print("Waiting for RUNNING status...")
    run_cmd(["runpodctl", "wait", "pod", pod_id, "--status", "RUNNING", "--timeout", "120"])
    show_url()

def stop():
    """Stop pod (stops billing)"""
    pod_id = get_pod_id()
    if not pod_id:
        print("No pod found.")
        return
    print(f"Stopping pod {pod_id}...")
    run_cmd(["runpodctl", "stop", "pod", pod_id])
    print("Stopped. Billing paused.")

def remove():
    """Delete pod permanently"""
    pod_id = get_pod_id()
    if not pod_id:
        print("No pod found.")
        return
    confirm = input(f"Delete pod {pod_id} permanently? (yes/no): ")
    if confirm.lower() == "yes":
        run_cmd(["runpodctl", "remove", "pod", pod_id])
        print("Deleted.")

def show_url():
    """Show public URL"""
    pod_id = get_pod_id()
    if not pod_id:
        print("No pod found.")
        return
    url = get_public_url(pod_id)
    if url:
        print(f"\n🔗 Public URL: {url}")
        print(f"📋 Test: curl {url}/api/tags")
        print(f"🤖 Agent: Select 'Ollama (Local)' → Paste URL → Connect")
    else:
        print("URL not ready yet. Wait a moment.")

def pull_model(model: str = DEFAULT_MODEL):
    """Pull model via RunPod terminal command"""
    pod_id = get_pod_id()
    if not pod_id:
        print("No pod found.")
        return
    
    url = get_public_url(pod_id)
    if not url:
        print("Pod not ready.")
        return
    
    # Use RunPod's exec API to run ollama pull
    print(f"Pulling {model}... (this takes 5-10 min for 70B)")
    print("Run this in RunPod Web Terminal instead for better progress:")
    print(f"  ollama pull {model}")

def status():
    """Show pod status"""
    pod_id = get_pod_id()
    if not pod_id:
        print("No pod deployed.")
        return
    
    pod = get_pod_status(pod_id)
    print(f"\nPod: {pod.get('name')}")
    print(f"ID: {pod_id}")
    print(f"Status: {pod.get('desiredStatus', 'unknown')}")
    print(f"GPU: {pod.get('machine', {}).get('gpuDisplayName', 'unknown')}")
    print(f"Cost: ${pod.get('costPerHr', 0):.3f}/hr")
    show_url()

def test_connection():
    """Test Ollama API"""
    pod_id = get_pod_id()
    if not pod_id:
        return
    url = get_public_url(pod_id)
    if not url:
        return
    
    try:
        r = requests.get(f"{url}/api/tags", timeout=10)
        if r.status_code == 200:
            models = r.json().get("models", [])
            print(f"✅ Connected! Models: {[m['name'] for m in models]}")
        else:
            print(f"❌ HTTP {r.status_code}")
    except Exception as e:
        print(f"❌ Connection failed: {e}")

if __name__ == "__main__":
    cmds = {
        "deploy": deploy,
        "start": start,
        "stop": stop,
        "remove": remove,
        "url": show_url,
        "status": status,
        "pull": lambda: pull_model(sys.argv[2] if len(sys.argv) > 2 else DEFAULT_MODEL),
        "test": test_connection,
    }
    
    if len(sys.argv) < 2 or sys.argv[1] not in cmds:
        print(f"Usage: python {sys.argv[0]} [deploy|start|stop|remove|url|status|pull|test]")
        print(f"Default model for pull: {DEFAULT_MODEL}")
        sys.exit(1)
    
    cmds[sys.argv[1]]()