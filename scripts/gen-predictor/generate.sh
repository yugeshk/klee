SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

CONSTRAINT_FILE=$1
PORT_LIST=$2

python3 $SCRIPT_DIR/gen_rules.py $PORT_LIST
pushd $SCRIPT_DIR >> /dev/null
  touch program_rules.ml
  make codegen.byte
popd >> /dev/null
$SCRIPT_DIR/codegen.byte $CONSTRAINT_FILE