{ imagename ? "luolabot" {},
  pkgs ? import (fetchTarball https://github.com/NixOS/nixpkgs/archive/refs/tags/23.11.tar.gz) {}
}:

let
  luola-bot-packages = import ./default.nix {};
  luolabot = pkgs.stdenv.mkDerivation {
    name = "luolaBot";
    buildInputs = [
      luola-bot-packages
    ];
    unpackPhase = "true";
    installPhase = ''
mkdir -p $out/bin
cp ${./luola_bot.py} $out/bin/luolabot
    '';
  };

in
pkgs.dockerTools.buildLayeredImage
  {
    name = imagename;
    contents = [luola-bot-packages luolabot];
    config = {
      Cmd = [
        "luolabot"
      ];
    };
  }
