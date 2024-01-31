{ pkgs ? import (fetchTarball https://github.com/NixOS/nixpkgs/archive/refs/tags/23.11.tar.gz) {} }:

let
  pythonDependencyList = pkgs.python310.withPackages (ps: [
    ps.requests
    ps.aiohttp
    ps.python-telegram-bot
    ps.pyyaml
  ]);

in
pythonDependencyList

