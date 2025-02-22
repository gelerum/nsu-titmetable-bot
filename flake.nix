{
  inputs = { nixpkgs.url = "github:nixos/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem
      (system:
        let
          pkgs = nixpkgs.legacyPackages.${system};
          venvDir = "./.venv";
        in
        {
          devShells.default = pkgs.mkShell {
            NIX_LD_LIBRARY_PATH = pkgs.lib.makeLibraryPath [
              pkgs.stdenv.cc.cc
              pkgs.zlib
            ];
            NIX_LD = pkgs.lib.fileContents "${pkgs.stdenv.cc}/nix-support/dynamic-linker";
            buildInputs = with pkgs; [ 
              python312 
            ];
            shellHook = ''
              export LD_LIBRARY_PATH=$NIX_LD_LIBRARY_PATH
              unset SOURCE_DATE_EPOCH

              if [ -d "${venvDir}" ]; then
                echo "Skipping venv creation, '${venvDir}' already exists"
              else
                echo "Creating new venv environment in path: '${venvDir}'"
                python -m venv "${venvDir}"
              fi

              source "${venvDir}/bin/activate"
            '';
          };
        }
      );
}
