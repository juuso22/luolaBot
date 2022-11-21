with import <nixpkgs> {};

let
  pythonEnv = python3.withPackages (ps: [
    ps.requests
  ]);
  pythonBuildEnv = python3.withPackages (ps: [
    ps.hatchling
  ]);
  habot = python3.pkgs.buildPythonPackage rec {
    format = "pyproject";
    pname = "habot";
    version = "0.0.3";

    src = python3.pkgs.fetchPypi {
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

in
{ pkgs ? import <nixpkgs> {} }:
pkgs.stdenv.mkDerivation {
  name = "luolaBot";
  buildInputs = [
    (python3.withPackages (ps: [
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
cp ${./luola_bot.py} $out/bin/luolabot
chmod 755 $out/bin/luolabot
    '';
}

