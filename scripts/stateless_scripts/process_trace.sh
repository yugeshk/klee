#!/bin/bash
inp_trace=$1
op_trace=$2
inp_metadata=$3
op_metadata=$4
arg=$5



if [ "$arg" != "verify-dpdk" ] && [ "$arg" != "verify-hardware" ]; then
        echo "Unsupported parameter"
	echo $arg
        exit
fi

if [ "$inp_trace" -nt "$op_trace" ]; then
  echo "$inp_trace -> $op_trace"
  echo "$inp_metadata -> $op_metadata"
  if [ "$arg" == "verify-dpdk" ]; then
   if grep -q "nf_core_process" $inp_trace; then  
    START=$(grep -n -m 1 "nf_core_process" $inp_trace |sed  's/\([0-9]*\).*/\1/')
   else
    echo "no packet processed"
    exit
   fi


   if grep -q "nf_core_process"  $inp_trace; then 
    END=$(grep -n "nf_core_process" $inp_trace | tail -1 |sed  's/\([0-9]*\).*/\1/')
   fi
   QUIT=$((END+1))
   sed -n ""$START","$END"p;"$QUIT"q" $inp_trace > $op_trace
   META_START=$(((START-2)*17+2))
   META_END=$(((END-1)*17+1))
   META_QUIT=$((META_END+1))
   sed -n ""$META_START","$META_END"p;"$META_QUIT"q" $inp_metadata > $op_metadata

  else
   if grep -q "rte_eth_rx_burst" $inp_trace; then  
    START=$(grep -n -m 1 "rte_eth_rx_burst" $inp_trace |sed  's/\([0-9]*\).*/\1/')
   elif grep -q "ixgbe_recv" $inp_trace; then
    START=$(grep -n -m 1 "ixgbe_recv" $inp_trace |sed  's/\([0-9]*\).*/\1/')
   else
    echo "no packet received"
    exit
   fi


   if grep -q "rte_eth_tx_burst"  $inp_trace; then 
    END=$(grep -n "rte_eth_tx_burst" $inp_trace | tail -1 |sed  's/\([0-9]*\).*/\1/')
   elif grep -q "ixgbe_xmit_pkts" $inp_trace; then
    END=$(grep -n "ixgbe_xmit_pkts" $inp_trace | tail -1 |sed  's/\([0-9]*\).*/\1/')
   else
    END=$(grep -n "exit@plt" $inp_trace | tail -1 |sed  's/\([0-9]*\).*/\1/')
   fi
   QUIT=$((END+1))
   sed -n ""$START","$END"p;"$QUIT"q" $inp_trace > $op_trace
   META_START=$(((START-2)*17+2))
   META_END=$(((END-1)*17+1))
   META_QUIT=$((META_END+1))
   sed -n ""$META_START","$META_END"p;"$META_QUIT"q" $inp_metadata > $op_metadata
 
  fi

fi
