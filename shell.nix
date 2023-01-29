with import <nixpkgs> {};
let
  luola-bot-packages = import ./default.nix {};
in
mkShell {
  buildInputs = [
    luola-bot-packages
  ];
}
