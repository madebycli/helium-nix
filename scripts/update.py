#!/usr/bin/env python3
"""Update version.nix from the latest signed Helium Linux release."""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

API_URL = "https://api.github.com/repos/imputnet/helium-linux/releases/latest"
EXPECTED_FINGERPRINT = "BE677C1989D35EAB2C5F26C9351601AD01D6378E"
ROOT = Path(__file__).resolve().parents[1]
VERSION_FILE = ROOT / "version.nix"
KEY_FILE = ROOT / "upstream" / "helium-signing-key.asc"
VERSION_RE = re.compile(r"^[0-9]+(?:\.[0-9]+){3}$")
ARCHITECTURES = {
    "x86_64-linux": "x86_64",
    "aarch64-linux": "arm64",
}


class UpdateError(RuntimeError):
    """A safe, user-facing update failure."""


def api_request(url: str) -> urllib.request.Request:
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "madebycli/helium-nix updater",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return urllib.request.Request(url, headers=headers)


def asset_request(url: str) -> urllib.request.Request:
    # Release assets are public. Do not forward the GitHub Actions token through
    # redirects to GitHub's asset-storage hosts.
    return urllib.request.Request(
        url,
        headers={"User-Agent": "madebycli/helium-nix updater"},
    )


def read_json(url: str) -> dict[str, Any]:
    try:
        with urllib.request.urlopen(api_request(url), timeout=45) as response:
            payload = json.load(response)
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as error:
        raise UpdateError(f"Could not read the official release API: {error}") from error

    if not isinstance(payload, dict):
        raise UpdateError("The official release API returned an unexpected payload")
    return payload


def latest_release() -> tuple[str, dict[str, tuple[str, str]]]:
    release = read_json(API_URL)
    if release.get("draft") is True or release.get("prerelease") is True:
        raise UpdateError("The latest GitHub release is not a stable published release")

    version = str(release.get("tag_name", ""))
    if not VERSION_RE.fullmatch(version):
        raise UpdateError(f"Unexpected Helium release tag: {version!r}")

    assets = release.get("assets")
    if not isinstance(assets, list):
        raise UpdateError("The official release contains no asset list")

    urls: dict[str, str] = {}
    for asset in assets:
        if not isinstance(asset, dict):
            continue
        name = asset.get("name")
        url = asset.get("browser_download_url")
        if isinstance(name, str) and isinstance(url, str):
            urls[name] = url

    resolved: dict[str, tuple[str, str]] = {}
    for system, platform in ARCHITECTURES.items():
        asset_name = f"helium-{version}-{platform}_linux.tar.xz"
        signature_name = f"{asset_name}.asc"
        if asset_name not in urls:
            available = ", ".join(sorted(urls))
            raise UpdateError(
                f"Expected official asset {asset_name!r} for {system}; "
                f"available assets: {available}"
            )
        if signature_name not in urls:
            raise UpdateError(
                f"The official detached signature {signature_name!r} is missing"
            )
        resolved[system] = (urls[asset_name], urls[signature_name])

    return version, resolved


def current_version() -> str:
    text = VERSION_FILE.read_text(encoding="utf-8")
    match = re.search(r'(?m)^\s*version\s*=\s*"([^"]+)";', text)
    if not match:
        raise UpdateError(f"Could not read the packaged version from {VERSION_FILE}")
    return match.group(1)


def download(url: str, target: Path) -> None:
    try:
        with urllib.request.urlopen(asset_request(url), timeout=180) as response:
            with target.open("wb") as output:
                shutil.copyfileobj(response, output, length=1024 * 1024)
    except (urllib.error.URLError, TimeoutError, OSError) as error:
        raise UpdateError(f"Could not download {url}: {error}") from error


def run(command: list[str], *, env: dict[str, str] | None = None) -> str:
    try:
        result = subprocess.run(
            command,
            check=True,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env,
        )
    except FileNotFoundError as error:
        raise UpdateError(f"Required command is missing: {command[0]}") from error
    except subprocess.CalledProcessError as error:
        detail = error.stderr.strip() or error.stdout.strip()
        raise UpdateError(f"Command failed: {' '.join(command)}\n{detail}") from error
    return result.stdout.strip()


def verify_signature(archive: Path, signature: Path, home: Path) -> None:
    home.mkdir(mode=0o700, exist_ok=True)
    run(["gpg", "--batch", "--homedir", str(home), "--import", str(KEY_FILE)])

    fingerprints = run(
        [
            "gpg",
            "--batch",
            "--homedir",
            str(home),
            "--with-colons",
            "--fingerprint",
        ]
    )
    imported = {
        fields[9]
        for line in fingerprints.splitlines()
        if line.startswith("fpr:")
        for fields in [line.split(":")]
        if len(fields) > 9
    }
    if EXPECTED_FINGERPRINT not in imported:
        raise UpdateError("The pinned Helium signing key has an unexpected fingerprint")

    run(
        [
            "gpg",
            "--batch",
            "--homedir",
            str(home),
            "--verify",
            str(signature),
            str(archive),
        ]
    )


def nix_hash(path: Path) -> str:
    value = run(["nix", "hash", "file", "--type", "sha256", "--sri", str(path)])
    if not value.startswith("sha256-"):
        raise UpdateError(f"Nix returned an unexpected hash: {value!r}")
    return value


def write_version(version: str, hashes: dict[str, str]) -> None:
    missing = [system for system in ARCHITECTURES if system not in hashes]
    if missing:
        raise UpdateError(f"Missing release hashes for: {', '.join(missing)}")

    lines = [
        "{",
        f'  version = "{version}";',
        "  hashes = {",
    ]
    for system in ARCHITECTURES:
        lines.append(f'    "{system}" = "{hashes[system]}";')
    lines.extend(["  };", "}", ""])
    VERSION_FILE.write_text("\n".join(lines), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="only report whether a newer stable release exists",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="re-verify and re-hash the current release even when versions match",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    packaged = current_version()
    latest, release_assets = latest_release()

    if args.check:
        if packaged == latest:
            print(f"Helium is current: {packaged}")
        else:
            print(f"Helium update available: {packaged} -> {latest}")
        return 0

    if packaged == latest and not args.force:
        print(f"Helium is current: {packaged}")
        return 0

    hashes: dict[str, str] = {}
    with tempfile.TemporaryDirectory(prefix="helium-update-") as directory:
        work = Path(directory)
        gnupg_home = work / "gnupg"

        for system, platform in ARCHITECTURES.items():
            archive_url, signature_url = release_assets[system]
            archive = work / f"helium-{latest}-{platform}_linux.tar.xz"
            signature = work / f"{archive.name}.asc"

            print(f"Downloading signed Helium release {latest} for {system}")
            download(archive_url, archive)
            download(signature_url, signature)
            verify_signature(archive, signature, gnupg_home)
            hashes[system] = nix_hash(archive)

    write_version(latest, hashes)
    print(f"Updated Helium metadata: {packaged} -> {latest}")
    for system in ARCHITECTURES:
        print(f"{system}: {hashes[system]}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except UpdateError as error:
        print(f"error: {error}", file=sys.stderr)
        raise SystemExit(1)
