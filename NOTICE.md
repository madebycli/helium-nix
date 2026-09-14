# Third-party notices

This repository provides independent Nix packaging for the official Helium Browser Linux binary releases.

- Helium Browser and the official Linux builds are developed by the `imputnet` project.
- Release archives are downloaded from `https://github.com/imputnet/helium-linux`.
- `x86_64-linux` uses the official `x86_64` Linux tarball.
- `aarch64-linux` uses the official `arm64` Linux tarball.
- Automated updates require and verify the detached signature published beside each supported tarball.
- The pinned signing-key fingerprint is `BE67 7C19 89D3 5EAB 2C5F 26C9 3516 01AD 01D6 378E`.
- Helium-specific code is declared GPL-3.0 by upstream.
- Imported Chromium and third-party components retain their respective licenses, including BSD-3-Clause components.

The packaging code maintained in this repository is licensed under GPL-3.0-only. That repository-level license does not replace or modify the licenses of the upstream binary and its bundled components.

This repository does not redistribute Helium release archives. Nix downloads the official fixed-output source directly from upstream and verifies its pinned SHA-256 hash.

Packaging in this repository is not maintained or endorsed by the Helium project.
