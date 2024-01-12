{ pkgs ? import (fetchTarball https://github.com/NixOS/nixpkgs/archive/refs/tags/23.11.tar.gz) {} }:

let
  pythonDependencyList = pkgs.python310.withPackages (ps: [
    ps.requests
    ps.aiohttp
    ps.python-telegram-bot
    ps.pyyaml
  ]);

  luolabot = pkgs.stdenv.mkDerivation {
    name = "luolaBot";
    buildInputs = [
      pythonDependencyList
    ];
    unpackPhase = "true";
    installPhase = ''
mkdir -p $out/bin
ln -sf ${./luola_bot.py} $out/bin/luolabot
    '';
  };
    
in
[
  luolabot
  pythonDependencyList
  pkgs.couchdb3
]
