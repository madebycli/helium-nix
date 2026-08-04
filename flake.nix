{
  description = "Native Nix package for the official Helium Browser Linux release";

  inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";

  outputs =
    { self, nixpkgs }:
    let
      system = "x86_64-linux";
      pkgs = nixpkgs.legacyPackages.${system};
      helium = import ./package.nix { inherit pkgs system; };
    in
    {
      packages.${system} = {
        inherit helium;
        default = helium;
      };

      apps.${system} = {
        helium = {
          type = "app";
          program = "${helium}/bin/helium";
        };
        default = self.apps.${system}.helium;
      };

      checks.${system} = {
        inherit helium;

        release-metadata = pkgs.runCommand "helium-release-metadata" { } ''
          set -euo pipefail
          version="${helium.version}"
          test -n "$version"
          test -x ${helium}/bin/helium
          ${helium}/bin/helium --version > "$out"
          grep -F "$version" "$out"
        '';
      };

      legacyPackages.${system}.helium = helium;

      overlays.default = final: _prev:
        nixpkgs.lib.optionalAttrs (final.stdenv.hostPlatform.system == system) {
          helium = import ./package.nix {
            pkgs = final;
            inherit system;
          };
        };

      devShells.${system}.default = pkgs.mkShell {
        packages = with pkgs; [
          git
          gnupg
          nixfmt-rfc-style
          python3
        ];
      };
    };
}
