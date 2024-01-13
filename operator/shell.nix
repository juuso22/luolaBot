with import <nixpkgs> {};
let
  luola-bot-operator-packages = import ./default.nix {};
in
mkShell {
  buildInputs = [
    luola-bot-operator-packages
    pkgs.k3s
  ];
}
