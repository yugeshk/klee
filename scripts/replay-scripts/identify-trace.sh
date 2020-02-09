!/bin/bash

# Master script to identify the precise execution path that an input takes through an NF.
# $1 - This is the NF
# $2 - This is the PCAP file that needs to be replayed

BOLT_DIR=~/projects/Bolt/bolt
KLEE_DIR=~/projects/Bolt/klee
REPLAY_SCRIPTS_DIR=$KLEE_DIR/scripts/replay-scripts

NF=$1
PCAP=$2

pushd $BOLT_DIR/nf/testbed/hard >> /dev/null

  bash bench.sh $NF replay-pcap-instr "null" $PCAP
  pushd $NF >> /dev/null
    bash $REPLAY_SCRIPTS_DIR/get-last-packet-trace.sh pincounts.log replay-trace
    python $REPLAY_SCRIPTS_DIR/demarcate-replay-trace.py replay-trace replay-demarcated
    python $REPLAY_SCRIPTS_DIR/cleanup-replay-trace.py replay-demarcated replay-branches

    bash ../test-bolt.sh $(basename $NF)
    python $REPLAY_SCRIPTS_DIR/match-branches.py
  
  popd >> /dev/null
   

popd >> /dev/null

