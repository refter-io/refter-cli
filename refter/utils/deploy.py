import json
import sys
from typing import Optional

import requests
from rich.console import Console

from refter.constants import API_ENDPOINT, API_HOST, CI, CI_BRANCH, CI_COMMIT


def upload_manifest(
    fn: str,
    api_token: str,
    branch: Optional[str],
    commit: Optional[str],
) -> None:
    console = Console()

    headers = {"x-api-token": api_token}
    params = {"commit": commit, "branch": branch}

    with open(fn, "rb") as file:
        data = json.loads(file.read())

        response = requests.post(
            f"{API_HOST}/{API_ENDPOINT}",
            json=data,
            headers=headers,
            params=params,
            timeout=180,
        )

        if response.status_code != 200:
            console.print(
                f"Failed to upload manifest: {response.text}",
                style="bold red",
            )
            sys.exit(1)

        console.print(
            "Manifest uploaded successfully!",
            style="bold green",
        )


def deploy(
    manifest_path: str,
    api_token: str,
    branch: Optional[str],
    commit: Optional[str],
) -> None:
    if CI:
        if not branch:
            branch = CI_BRANCH

        if not commit:
            commit = CI_COMMIT

    upload_manifest(
        manifest_path,
        api_token,
        branch,
        commit,
    )
