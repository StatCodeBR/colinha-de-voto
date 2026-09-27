{
  description = "Colinha do Voto: ambiente de desenvolvimento";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
  };

  outputs =
    { self, nixpkgs }:
    let
      systems = [
        "x86_64-linux"
        "aarch64-linux"
        "x86_64-darwin"
        "aarch64-darwin"
      ];
      forAllSystems = f: nixpkgs.lib.genAttrs systems (system: f nixpkgs.legacyPackages.${system});
    in
    {
      devShells = forAllSystems (
        pkgs:
        let
          lib = pkgs.lib;
          # Python vem do Nix; as bibliotecas (pandas, pyarrow...) vêm do uv, travadas no uv.lock.
          python = pkgs.python312;
        in
        {
          default = pkgs.mkShell {
            packages = [
              python
              pkgs.uv
              pkgs.just
              pkgs.ruff
              pkgs.nodejs # só para o OpenSpec (npm)
              pkgs.git
              pkgs.unzip
            ];

            shellHook = ''
              # uv usa o Python do Nix e nunca baixa outro
              export UV_PYTHON="${python}/bin/python3"
              export UV_PYTHON_DOWNLOADS=never

              # npm instala o OpenSpec dentro do projeto (o store do Nix é somente leitura)
              export NPM_CONFIG_PREFIX="$PWD/.npm-global"
              export PATH="$NPM_CONFIG_PREFIX/bin:$PATH"
            ''
            + lib.optionalString pkgs.stdenv.isLinux ''
              # wheels manylinux (pandas, pyarrow) precisam de libstdc++ e zlib no NixOS
              export LD_LIBRARY_PATH="${
                lib.makeLibraryPath [
                  pkgs.stdenv.cc.cc.lib
                  pkgs.zlib
                ]
              }''${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
            ''
            + ''
              echo "Colinha do Voto: rode 'just' para ver os comandos."
            '';
          };
        }
      );
    };
}
