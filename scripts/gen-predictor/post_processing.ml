open Core
open Ir


let () =
  let ip_file = Sys.argv.(1) in
  let ip_file_lines = In_channel.read_all ip_file in
  let branches_raw = Str.split (Str.regexp "\n+") ip_file_lines in
  let branches =  List.map branches_raw ~f:(fun exp -> render_tterm (Import.parse_condition exp)) in
  List.iter branches ~f:(fun py_exp -> Printf.printf "%s" py_exp)