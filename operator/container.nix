{ imagename ? "luolabot-operator" }:
let
  pkgs = import (fetchTarball https://github.com/NixOS/nixpkgs/archive/refs/tags/23.11.tar.gz) {};
  luola-bot-operator-packages = import ./default.nix {};
  operatorFile = pkgs.writeTextDir "luola_bot_operator.py" (builtins.readFile ./luola_bot_operator.py);

in
pkgs.dockerTools.buildLayeredImage
  {
    name = imagename;
    contents = [
      operatorFile
      luola-bot-operator-packages
    ];
    config = {
      Cmd = [
        "python3"
        "/luola_bot_operator.py"
      ];
    };
  }
