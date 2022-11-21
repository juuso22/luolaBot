with import <nixpkgs> {};
let
  luola-bot-package = import ./default.nix {};
in
mkShell {
  buildInputs = [
    luola-bot-package
  ];
}
