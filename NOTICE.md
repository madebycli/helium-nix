# Third-party notices

This repository provides independent Nix packaging for the official Helium Browser Linux binary release.

- Helium Browser and the official Linux builds are developed by the `imputnet` project.
- Release archives are downloaded from `https://github.com/imputnet/helium-linux`.
- Automated updates require the detached signature published beside the official tarball.
- The pinned signing-key fingerprint is `BE67 7C19 89D3 5EAB 2C5F 26C9 3516 01AD 01D6 378E`.
- Helium-specific code is declared GPL-3.0 by upstream.
- Imported Chromium and third-party components retain their respective licenses, including BSD-3-Clause components.

This repository does not redistribute the Helium release archive. Nix downloads the official fixed-output source directly from upstream and verifies its pinned SHA-256 hash.

Packaging in this repository is not maintained or endorsed by the Helium project.
