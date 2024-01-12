{ pkgs ? import (fetchTarball https://github.com/NixOS/nixpkgs/archive/refs/tags/23.11.tar.gz) {} }:

let
  pythonEnv = pkgs.python310.withPackages (ps: [
    ps.requests
  ]);
  pythonBuildEnv = pkgs.python310.withPackages (ps: [
    ps.hatchling
  ]);
  habot = pkgs.python310.pkgs.buildPythonPackage rec {
    format = "pyproject";
    pname = "habot";
    version = "0.0.3";

    src = pkgs.python310.pkgs.fetchPypi {
      inherit pname version;
      sha256 = "e0f14824eb2b20a627ad4abe467deaa27f0b0b0dd1ab98472321827889ee62b3";
    };

    buildInputs = [ pythonBuildEnv ];
    propagatedBuildInputs = [ pythonEnv ];

    meta = {
      homepage = "https://github.com/juuso22/habot";
      description = "A Python package to run highly available Telegram bots";
    };
  };


  luolabot = pkgs.stdenv.mkDerivation {
    name = "luolaBot";
    buildInputs = [
      (pkgs.python310.withPackages (ps: [
        ps.requests
        ps.aiohttp
        ps.python-telegram-bot
        ps.pyyaml
        habot
      ]))
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
  (pkgs.python310.withPackages (ps: [
        ps.requests
        ps.aiohttp
        ps.python-telegram-bot
        ps.pyyaml
        habot
  ]))
]
