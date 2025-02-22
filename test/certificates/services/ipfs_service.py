import requests
import os
from django.conf import settings

def upload_to_ipfs(file_content):
    try:
        response = requests.post(
            f"http://{settings.IPFS_HOST}:{settings.IPFS_PORT}/api/v0/add",
            files={"file": file_content}
        )
        
        if response.status_code == 200:
            return response.json()["Hash"]
        return None
    except Exception as e:
        print(f"Error uploading to IPFS: {str(e)}")
        return None

def get_from_ipfs(ipfs_hash):
    try:
        response = requests.get(
            f"http://{settings.IPFS_HOST}:{settings.IPFS_PORT}/api/v0/cat?arg={ipfs_hash}"
        )
        
        if response.status_code == 200:
            return response.content
        return None
    except Exception as e:
        print(f"Error getting from IPFS: {str(e)}")
        return None 