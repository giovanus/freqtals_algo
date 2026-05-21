import requests
import json

GITHUB_API = "https://api.github.com/search/repositories"

params = {
    "q": "nodejs api language:javascript stars:>50",
    "sort": "stars",
    "order": "desc",
    "per_page": 3
}

response = requests.get(GITHUB_API, params=params)

data = response.json()

repos = []

for repo in data["items"]:
    repos.append(repo["clone_url"])

with open("repos_list.json", "w") as f:
    json.dump(repos, f, indent=2)

print(f"{len(repos)} repositories saved")