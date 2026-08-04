<p align="center">
  <img src="assets/readme-banner.svg" alt="helium-nix — Helium Browser for Nix and NixOS" width="100%">
</p>

<p align="center">
  <a href="https://github.com/madebycli/helium-nix/actions/workflows/ci.yml"><img alt="CI" src="https://github.com/madebycli/helium-nix/actions/workflows/ci.yml/badge.svg?branch=main"></a>
  <a href="https://github.com/madebycli/helium-nix/actions/workflows/update-upstream.yml"><img alt="Upstream update" src="https://github.com/madebycli/helium-nix/actions/workflows/update-upstream.yml/badge.svg?branch=main"></a>
  <img alt="Nix Flake" src="https://img.shields.io/badge/Nix-Flake-5277C3?logo=nixos&logoColor=white">
  <img alt="Platform" src="https://img.shields.io/badge/platform-x86__64--linux-8c7cff">
</p>

<p align="center">
  Native, reproducible Nix packaging for the official Helium Browser Linux release.
</p>

## Quick start

Run Helium without installing it:

```bash
nix run github:madebycli/helium-nix
```

Install it into the current Nix profile:

```bash
nix profile add github:madebycli/helium-nix#helium
helium
```

Upgrade profile-managed packages:

```bash
nix profile upgrade --all --refresh
```

## What this repository provides

- A native Nix package built from Helium's official Linux tarball
- Desktop entry and application icon integration
- Runtime libraries patched into a reproducible Nix closure
- A flake package, app, overlay, checks, and development shell
- Daily upstream release checks
- A safe manual update button in GitHub Actions
- Signature verification with Helium's published signing key
- Build and runtime validation before any automated update reaches `main`

This repository packages Helium; it does not build Chromium or Helium from source.

## NixOS

Add the flake input and install the package:

```nix
{
  inputs.helium-nix.url = "github:madebycli/helium-nix";

  environment.systemPackages = [
    inputs.helium-nix.packages.${pkgs.system}.helium
  ];
}
```

## Overlay

```nix
{
  nixpkgs.overlays = [ inputs.helium-nix.overlays.default ];
  environment.systemPackages = [ pkgs.helium ];
}
```

## Flake outputs

```text
packages.x86_64-linux.{default,helium}
apps.x86_64-linux.{default,helium}
checks.x86_64-linux
legacyPackages.x86_64-linux.helium
overlays.default
devShells.x86_64-linux.default
```

## Automatic updates

The `Update upstream release` workflow runs once per day at `01:47 UTC`, which is approximately `03:47` in Berlin during daylight-saving time and `02:47` in winter.

The same workflow can be started manually:

```text
Actions → Update upstream release → Run workflow
```

A manual run does not move or cancel the next scheduled run. The workflow uses one concurrency group, so scheduled and manual runs cannot publish over each other.

For a new release, the workflow:

1. reads the latest stable release from `imputnet/helium-linux`;
2. selects the exact `x86_64` Linux tarball and detached signature;
3. verifies the tarball against Helium's published signing key;
4. computes the Nix SHA-256 hash locally;
5. changes only `version.nix`;
6. evaluates, checks, builds, and launches the packaged version check;
7. confirms that `main` did not move during validation;
8. publishes the update only after every validation succeeds.

Running the workflow while Helium is already current is safe and produces no commit.

## Local update check

```bash
nix develop
python3 scripts/update.py --check
```

Apply the latest release locally:

```bash
python3 scripts/update.py
nix flake check --print-build-logs
nix build .#helium --print-build-logs
./result/bin/helium --version
```

The updater requires Nix and GnuPG because release signatures are mandatory.

## Development

```bash
nix flake lock
git diff --exit-code -- flake.lock
nix flake show --no-write-lock-file
nix flake check --no-write-lock-file --print-build-logs
nix build .#helium --no-write-lock-file --print-build-logs
./result/bin/helium --version
```

## Upstream and licensing

Helium Browser and its official Linux builds are maintained by the [`imputnet`](https://github.com/imputnet) project. This repository is an independent Nix packaging integration and is not an official Helium distribution channel.

See [`NOTICE.md`](NOTICE.md) for source, signature, and licensing information.
