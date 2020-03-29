SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

pushd $SCRIPT_DIR >> /dev/null
  make codegen.byte
popd >> /dev/null
$SCRIPT_DIR/codegen.byte $@