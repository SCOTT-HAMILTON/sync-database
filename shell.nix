{  }:
let
  pkgs = import <nixpkgs-unstable> {};
  localShamilton = import ~/GIT/nur-packages { };
  customPython = pkgs.python3.buildEnv.override {
    extraLibs = with pkgs.python3Packages; [
      setuptools
      black
    ];
  };
in
with pkgs; mkShell {
  buildInputs = [
    localShamilton.merge-keepass
    localShamilton.parallel-ssh
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

