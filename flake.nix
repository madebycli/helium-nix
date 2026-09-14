{
  description = "Native Nix package for the official Helium Browser Linux release";

  inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";

  outputs =
    { self, nixpkgs }:
    let
      systems = [
        "x86_64-linux"
        "aarch64-linux"
      ];
      forAllSystems = nixpkgs.lib.genAttrs systems;
      packageFor =
        system:
        let
          pkgs = nixpkgs.legacyPackages.${system};
        in
        import ./package.nix { inherit pkgs system; };
    in
    {
      packages = forAllSystems (
        system:
        let
          helium = packageFor system;
        in
        {
          inherit helium;
          default = helium;
        }
      );

      apps = forAllSystems (
        system:
        let
          helium = packageFor system;
        in
        {
          helium = {
            type = "app";
            program = "${helium}/bin/helium";
          };
          default = self.apps.${system}.helium;
        }
      );

      checks = forAllSystems (
        system:
        let
          pkgs = nixpkgs.legacyPackages.${system};
          helium = packageFor system;
        in
        {
          inherit helium;

          release-metadata = pkgs.runCommand "helium-release-metadata" { } ''
            set -euo pipefail
            version="${helium.version}"
            test -n "$version"
            test -x ${helium}/bin/helium
            ${helium}/bin/helium --version > "$out"
            grep -F "$version" "$out"
          '';
        }
      );

      legacyPackages = forAllSystems (system: {
        helium = packageFor system;
      });

      overlays.default = final: _prev:
        nixpkgs.lib.optionalAttrs (builtins.elem final.stdenv.hostPlatform.system systems) {
          helium = import ./package.nix {
            pkgs = final;
            system = final.stdenv.hostPlatform.system;
          };
        };

      devShells = forAllSystems (
        system:
        let
          pkgs = nixpkgs.legacyPackages.${system};
        in
        {
          default = pkgs.mkShell {
            packages = with pkgs; [
              git
              gnupg
              nixfmt-rfc-style
              python3
            ];
          };
        }
      );
    };
}
