<p align="center">
  <img src="assets/readme-banner.svg" alt="helium-nix — Helium Browser for Nix and NixOS" width="100%">
</p>

<p align="center">
  <a href="https://github.com/madebycli/helium-nix/actions/workflows/ci.yml"><img alt="CI" src="https://github.com/madebycli/helium-nix/actions/workflows/ci.yml/badge.svg?branch=main"></a>
  <a href="https://github.com/madebycli/helium-nix/actions/workflows/update-upstream.yml"><img alt="Upstream update" src="https://github.com/madebycli/helium-nix/actions/workflows/update-upstream.yml/badge.svg?branch=main"></a>
  <img alt="Nix Flake" src="https://img.shields.io/badge/Nix-Flake-5277C3?logo=nixos&logoColor=white">
  <img alt="Platform" src="https://img.shields.io/badge/platform-x86__64%20%7C%20arm64-8c7cff">
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

## Supported systems

- `x86_64-linux`
- `aarch64-linux`

Both architectures use the matching official signed Linux tarball and are tested on native GitHub-hosted Linux runners.

## What this repository provides

- Native Nix packages built from Helium's official Linux tarballs
- Desktop entry and application icon integration
- Runtime libraries patched into a reproducible Nix closure
- Flake packages, apps, overlays, checks, and development shells for both supported Linux architectures
- Daily upstream release checks
- A safe manual update button in GitHub Actions
- Signature verification with Helium's published signing key
- Native x86_64 and ARM64 build/runtime validation in CI

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

For both `x86_64-linux` and `aarch64-linux`:

```text
packages.<system>.{default,helium}
apps.<system>.{default,helium}
checks.<system>
legacyPackages.<system>.helium
devShells.<system>.default
```

## Automatic updates

The `Update upstream release` workflow runs once per day at `01:47 UTC`, which is approximately `03:47` in Berlin during daylight-saving time and `02:47` in winter.

The same workflow can be started manually:

```text
Actions → Update upstream release → Run workflow
```

A manual run does not move or cancel the next scheduled run. The workflow uses one concurrency group, so scheduled and manual runs cannot publish over each other.

For a new release, the updater:

1. reads the latest stable release from `imputnet/helium-linux`;
2. requires the exact `x86_64` and `arm64` Linux tarballs plus their detached signatures;
3. verifies both tarballs against Helium's published signing key;
4. computes and records a separate Nix SHA-256 hash for each supported system;
5. changes only `version.nix`;
6. evaluates, checks, builds, and launches the packaged version check before publication;
7. confirms that `main` did not move during validation;
8. publishes the update only after validation succeeds.

The regular CI then builds and executes the package natively on both x86_64 and ARM64. Running the update workflow while Helium is already current is safe and produces no commit.

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

## Licensing

The packaging code in this repository is licensed under GPL-3.0-only. Helium Browser, Chromium, and bundled third-party components retain their own upstream licenses.

Helium Browser and its official Linux builds are maintained by the [`imputnet`](https://github.com/imputnet) project. This repository is an independent Nix packaging integration and is not an official Helium distribution channel.

See [`NOTICE.md`](NOTICE.md) for source, signature, and upstream licensing information.
