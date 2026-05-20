import sys
import os
import requests
import subprocess

def get_git_token():
    try:
        # Query the local Git Credential Manager for the GitHub token
        proc = subprocess.run(
            ['git', 'credential', 'fill'],
            input="url=https://github.com\n",
            capture_output=True,
            text=True,
            check=True
        )
        for line in proc.stdout.splitlines():
            if line.startswith('password='):
                return line.split('=', 1)[1].strip()
    except Exception as e:
        print("Warning: Could not retrieve GitHub token from git credentials:", e)
    return None

if len(sys.argv) < 2:
    print("Error: Tag name required.")
    sys.exit(1)

tag = sys.argv[1]
owner = "3122380192"
repo = "Ai-La-Vua-Li-Don"
file_path = os.path.abspath("Tx6.exe")

if not os.path.exists(file_path):
    print(f"Error: Executable '{file_path}' not found. Please build first.")
    sys.exit(1)

token = get_git_token()
if not token:
    print("Error: GitHub token not found. Please ensure you are logged into Git on this machine.")
    sys.exit(1)

headers = {
    "Authorization": f"token {token}",
    "Accept": "application/vnd.github.v3+json"
}

print(f"Creating release {tag}...")
release_data = {
    "tag_name": tag,
    "target_commitish": "main",
    "name": f"Ai La Vua Li Don {tag}",
    "body": f"Release containing the built Tx6.exe executable for version {tag}.",
    "draft": False,
    "prerelease": False
}

r = requests.post(f"https://api.github.com/repos/{owner}/{repo}/releases", headers=headers, json=release_data)
if r.status_code not in (200, 201):
    print("Failed to create release:", r.text)
    sys.exit(1)

release_json = r.json()
release_id = release_json["id"]
upload_url = release_json["upload_url"].split("{")[0]
print(f"Release created successfully (ID: {release_id}).")

print(f"Uploading {os.path.basename(file_path)}...")
upload_headers = {
    "Authorization": f"token {token}",
    "Content-Type": "application/octet-stream"
}

with open(file_path, "rb") as f:
    upload_r = requests.post(
        f"{upload_url}?name={os.path.basename(file_path)}",
        headers=upload_headers,
        data=f
    )

if upload_r.status_code in (200, 201):
    print("SUCCESS: Tx6.exe uploaded successfully to Release assets!")
    print("Download URL:", upload_r.json().get("browser_download_url"))
else:
    print("Failed to upload asset:", upload_r.text)
    sys.exit(1)
