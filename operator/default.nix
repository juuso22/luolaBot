{ pkgs ? import (fetchTarball https://github.com/NixOS/nixpkgs/archive/cf63ade6f74bbc9d2a017290f1b2e33e8fbfa70a.tar.gz) {} }:

let
  buildInputs = [
    (pkgs.python310.withPackages (ps: [
      ps.kubernetes
    ]))
  ];
    
in
[
  buildInputs
]
