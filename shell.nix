{  }:
let
  pkgs = import <nixpkgs-unstable> {};
  shamilton = import (builtins.fetchTarball {
    url = "https://github.com/SCOTT-HAMILTON/nur-packages-template/tarball/3697820";
    sha256 = "0far417l4way1fzb097s9cqda2k2f5r6szvm4mml4cagd21sc936";
  }) { inherit pkgs; nixosVersion = "nixpkgs-unstable"; };
  customPython = pkgs.python3.buildEnv.override {
    extraLibs = with pkgs.python3Packages; [
      setuptools
      black
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
    format(){
      black .
    }
  '';
}

