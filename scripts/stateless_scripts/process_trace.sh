#!/bin/bash
inp=$1
op=$2
arg=$3

if [ "$arg" != "verify-dpdk" ] && [ "$arg" != "verify-hardware" ]; then
        echo "Unsupported parameter"
        exit
fi

if [ "$inp" -nt "$op" ]; then
  echo "$inp -> $op"

  if [ "$arg" == "verify-dpdk" ]; then
   if grep -q "nf_core_process" $1; then  
    START=$(grep -n -m 1 "nf_core_process" $1 |sed  's/\([0-9]*\).*/\1/')
   else
    echo "no packet processed"
    echo " " > $2
    exit
   fi


   if grep -q "nf_core_process"  $1; then 
    END=$(grep -n "nf_core_process" $1 | tail -1 |sed  's/\([0-9]*\).*/\1/')
   fi
   ENDEND=$((END+1))
   sed -n ""$START","$END"p;"$ENDEND"q" $1 > $2

  else
   if grep -q "rte_eth_rx_burst" $1; then  
    START=$(grep -n -m 1 "rte_eth_rx_burst" $1 |sed  's/\([0-9]*\).*/\1/')
   elif grep -q "ixgbe_recv" $1; then
    START=$(grep -n -m 1 "ixgbe_recv" $1 |sed  's/\([0-9]*\).*/\1/')
   else
    echo "no packet received"
    echo " " > $2
    exit
   fi


   if grep -q "rte_eth_tx_burst"  $1; then 
    END=$(grep -n "rte_eth_tx_burst" $1 | tail -1 |sed  's/\([0-9]*\).*/\1/')
   elif grep -q "ixgbe_xmit_pkts" $1; then
    END=$(grep -n "ixgbe_xmit_pkts" $1 | tail -1 |sed  's/\([0-9]*\).*/\1/')
   else
    END=$(grep -n "exit@plt" $1 | tail -1 |sed  's/\([0-9]*\).*/\1/')
   fi
   ENDEND=$((END+1))
   sed -n ""$START","$END"p;"$ENDEND"q" $1 > $2
 
  fi

fi
