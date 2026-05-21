import os
import json
import subprocess

REPO_DIR = "repos"

os.makedirs(REPO_DIR, exist_ok=True)

with open("repos_list.json") as f:
    repos = json.load(f)

for repo in repos:

    name = repo.split("/")[-1].replace(".git","")
    path = os.path.join(REPO_DIR, name)

    if os.path.exists(path):
        print("Already cloned:", name)
        continue

    print("Cloning:", repo)

    subprocess.run(["git","clone","--depth", "1",repo,path])