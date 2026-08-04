{ pkgs, system }:

let
  inherit (pkgs) lib;
  release = import ./version.nix;

  platform =
    {
      x86_64-linux = "x86_64";
    }
    .${system} or (throw "Helium is not packaged for ${system}");

  src = pkgs.fetchurl {
    url = "https://github.com/imputnet/helium-linux/releases/download/${release.version}/helium-${release.version}-${platform}_linux.tar.xz";
    inherit (release) hash;
  };

  runtimeLibraries = with pkgs; [
    alsa-lib
    at-spi2-atk
    at-spi2-core
    atk
    cairo
    cups
    dbus
    expat
    fontconfig
    freetype
    gdk-pixbuf
    glib
    gtk3
    libdrm
    libnotify
    libx11
    libxcb
    libxcomposite
    libxdamage
    libxext
    libxfixes
    libxkbcommon
    libxrandr
    mesa
    nspr
    nss
    pango
    stdenv.cc.cc.lib
    systemd
    wayland
    zlib
  ];
in
pkgs.stdenv.mkDerivation {
  pname = "helium";
  inherit (release) version;
  inherit src;

  strictDeps = true;
  sourceRoot = ".";

  nativeBuildInputs = [
    pkgs.autoPatchelfHook
    pkgs.makeWrapper
  ];

  buildInputs = runtimeLibraries;

  # The official archive includes optional Qt input-method shims. Helium itself
  # is Chromium/GTK based, so these optional Sonames are not runtime requirements.
  autoPatchelfIgnoreMissingDeps = [
    "libQt5Core.so.5"
    "libQt5Gui.so.5"
    "libQt5Widgets.so.5"
    "libQt6Core.so.6"
    "libQt6Gui.so.6"
    "libQt6Widgets.so.6"
  ];

  installPhase = ''
    runHook preInstall

    mkdir -p "$out/opt/helium" "$out/bin"

    heliumRoot="$(find . -maxdepth 3 -type f -name helium -printf '%h\n' | head -n1)"
    if [ -z "$heliumRoot" ]; then
      echo "Helium binary not found in the official release archive" >&2
      find . -maxdepth 4 -type f -print >&2
      exit 1
    fi

    cp -a "$heliumRoot/." "$out/opt/helium/"

    makeWrapper "$out/opt/helium/helium" "$out/bin/helium" \
      --prefix LD_LIBRARY_PATH : "${lib.makeLibraryPath runtimeLibraries}" \
      --prefix PATH : "${lib.makeBinPath [ pkgs.coreutils pkgs.xdg-utils ]}" \
      --add-flags "--disable-breakpad"

    desktopFile="$(find "$out/opt/helium" -maxdepth 4 -type f -name '*.desktop' | head -n1 || true)"
    if [ -n "$desktopFile" ]; then
      install -Dm644 "$desktopFile" "$out/share/applications/helium.desktop"
      substituteInPlace "$out/share/applications/helium.desktop" \
        --replace-warn 'Exec=helium' "Exec=$out/bin/helium"
    fi

    for size in 16 24 32 48 64 128 256; do
      icon="$(find "$out/opt/helium" -type f \
        \( -name "product_logo_$size.png" -o -name "helium_$size.png" \) \
        | head -n1 || true)"
      if [ -n "$icon" ]; then
        install -Dm644 "$icon" \
          "$out/share/icons/hicolor/''${size}x''${size}/apps/helium.png"
      fi
    done

    runHook postInstall
  '';

  doInstallCheck = true;
  installCheckPhase = ''
    runHook preInstallCheck
    test -x "$out/bin/helium"
    test -x "$out/opt/helium/helium"
    "$out/bin/helium" --version >/dev/null
    runHook postInstallCheck
  '';

  passthru = {
    inherit src;
    updateScript = ./scripts/update.py;
  };

  meta = {
    description = "Fast, private Chromium-based web browser";
    homepage = "https://github.com/imputnet/helium-linux";
    license = with lib.licenses; [ gpl3Only bsd3 ];
    mainProgram = "helium";
    platforms = [ "x86_64-linux" ];
    sourceProvenance = [ lib.sourceTypes.binaryNativeCode ];
  };
}
