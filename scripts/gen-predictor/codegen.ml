open Core
open Ir

type branch = {cond : tterm list; perf : int}

let parse_branches file =
  let branches_raw = Str.split (Str.regexp "\n+") file in
  let branches = List.map branches_raw ~f:(fun br ->
      let fields = Str.split (Str.regexp ", *") br in
      match fields with
      | [cond_raw; perf_raw] ->
        let cond_str = Str.split (Str.regexp " *\*\*AND\*\* *") cond_raw in
        let perf = int_of_string perf_raw in
        let cond = List.map cond_str ~f:(fun str ->
          {v = Id str; t = Boolean})
        in
        {cond;perf}
      | _ -> failwith (br ^ " is a malformed branch specification."))
  in
  branches

let gen_predictor branches =
  String.concat ~sep:"\nelse "
    (List.map branches ~f:(fun br ->
         "if " ^ (String.concat ~sep: " and "
                    (List.map br.cond ~f:(fun cnd ->
                         "(" ^ (render_tterm cnd) ^ ")"))) ^
         " : return " ^
         (string_of_int br.perf)
       )) ^ "\n"


let convert_constraints_to_predictor in_fname out_fname =
  match Sys.file_exists in_fname with
  | `No | `Unknown -> failwith ("Source constraints faile " ^ out_fname ^ "does not exist")
  | `Yes -> begin
      print_endline ("generating predictor code in " ^
                     out_fname ^ " based on constraints in " ^
                     in_fname);
      let constraints = In_channel.read_all in_fname in
      let branches = parse_branches constraints in
      let predictor = gen_predictor branches in
      Out_channel.write_all out_fname predictor
    end

let () =
  let fname = Sys.argv.(1) in
  let out_fname = fname ^ ".py" in
  convert_constraints_to_predictor fname out_fname
