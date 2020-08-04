open Core
open Ir

let () =
  let fname = Sys.argv.(1) in
  let debug =
    ((Array.length Sys.argv) = 3) &&
    (String.equal Sys.argv.(2) "-debug")
  in
  let out_fname = fname ^ ".py" in
  Codegen_rules.convert_constraints_to_predictor fname out_fname debug
