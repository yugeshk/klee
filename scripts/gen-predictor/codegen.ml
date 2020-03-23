open Core
open Ir

let () =
  let fname = Sys.argv.(1) in
  let out_fname = fname ^ ".py" in
  match Sys.file_exists fname with
  | `No | `Unknown -> failwith ("Source constraints faile " ^ fname ^ "does not exist")
  | `Yes -> begin
      print_endline ("generating predictor code in " ^ out_fname ^ " based on constraints in " ^ fname)
      end
  (* Out_channel.write_all "hello" *)
