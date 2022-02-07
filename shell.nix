{  }:
let
  pkgs = import <nixpkgs-unstable> {};
  shamilton = import (builtins.fetchTarball {
    url = "https://github.com/SCOTT-HAMILTON/nur-packages-template/tarball/5d52675";
    sha256 = "18wj7g0w148xbjxjka1fag1wm7ibr3ph9hx1xg5g6wkwyl7zkqvk";
  }) { inherit pkgs; nixosVersion = "nixpkgs-unstable"; };
  customPython = pkgs.python3.buildEnv.override {
    extraLibs = with pkgs.python3Packages; [
      setuptools
    ];
  };
in
with pkgs; mkShell {
  buildInputs = [
    shamilton.merge-keepass
    shamilton.parallel-ssh
    libssh2
    customPython
  ];
  shellHook = ''
    export LD_LIBRARY_PATH=${libssh2}/lib
    run_test(){
      python tests.py
    }
  '';
}

