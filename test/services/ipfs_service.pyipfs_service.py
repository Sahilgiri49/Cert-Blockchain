import requests
import os
from dotenv import load_dotenv

# Load .env variables
load_dotenv()

IPFS_API_URL = os.getenv("IPFS_API_URL")
PROJECT_ID = os.getenv("IPFS_PROJECT_ID")
PROJECT_SECRET = os.getenv("IPFS_PROJECT_SECRET")

# Upload File to IPFS
def upload_to_ipfs(file_path):
    with open(file_path, "rb") as file:
        response = requests.post(
            f"{IPFS_API_URL}/api/v0/add",
            files={"file": file},
            auth=(PROJECT_ID, PROJECT_SECRET),
        )

    if response.status_code == 200:
        return response.json()["Hash"]  # IPFS CID (Content Identifier)
    else:
        return None

# Get File from IPFS
def get_from_ipfs(cid):
    return f"https://ipfs.io/ipfs/{cid}"