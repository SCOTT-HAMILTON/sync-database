{  }:
let
  pkgs = import <nixpkgs-unstable> {};
  shamilton = import (builtins.fetchTarball {
    url = "https://github.com/SCOTT-HAMILTON/nur-packages-template/tarball/7085556";
    sha256 = "03haqvsc9nklklj626nvz9qq9yrzv53pxm4gq32k5m0g6pd4ykdc";
  }) { inherit pkgs; };
in
with pkgs; mkShell {
  buildInputs = [
    shamilton.merge-keepass
    shamilton.parallel-ssh
    libssh2
  ];
  shellHook = ''
    export LD_LIBRARY_PATH=${libssh2}/lib
    run_test(){
      python tests.py
    }
  '';
}

