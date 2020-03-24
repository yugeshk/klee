open Core
open Ir

type if_tree = Branch of term * if_tree * if_tree
             | Leaf of int

let rec gen_if_tree branches cumul_cnd =
  let find_agreeing_branches cnd =
    List.filter ~f:(fun b -> List.exists Import.(b.cond)
                       ~f:(fun c -> term_eq c cnd))
  in
  match branches with
  | hd :: tl -> begin
    match List.find Import.(hd.cond) ~f:(fun c ->
        not (List.exists cumul_cnd ~f:(term_eq c)))
    with
    | Some pro ->
      let contra = match pro with
        | Not x -> x.v
        | x -> Not {v=x; t=Boolean}
      in
      let then_branch = gen_if_tree
          (hd::(find_agreeing_branches pro tl))
          (pro::cumul_cnd)
      in
      let else_branch = gen_if_tree
          (find_agreeing_branches contra tl)
          (contra::cumul_cnd)
      in
      Branch (pro, then_branch, else_branch)
    | None -> Leaf hd.perf
    end
  | [] -> Leaf (-1)

let rec render_if_tree tree ident =
  match tree with
  | Branch (c, t, e) ->
    ident ^ "if " ^ (render_term c) ^ ":\n" ^
    (render_if_tree t (ident ^ "    ")) ^ "\n" ^
    ident ^ "else:\n" ^
    (render_if_tree e (ident ^ "    "))
  | Leaf x -> ident ^ "return " ^ (string_of_int x)

let rewrite_cond = call_recursively_on_term (function
    | Utility (Slice ({v=Id "user_buf";t=_}, 12, 16)) ->
      Some (Str_idx ({v=Str_idx ({v=Id "pkt";t=Unknown}, "ether");t=Unknown},
                     "type"))
    | Utility (Slice ({v=Id "buf_value";t=_}, 32, 32)) ->
      Some (Str_idx ({v=Id "mbuf";t=Unknown}, "packet_type"))
    | _ -> None)

let rec rewrite_if_tree = function
  | Branch (c, t, e) ->
    Branch ( (rewrite_cond {v=c;t=Boolean}).v,
            rewrite_if_tree t, rewrite_if_tree e)
  | Leaf x -> Leaf x


let gen_predictor branches =
  render_if_tree (rewrite_if_tree (gen_if_tree branches [])) ""

let convert_constraints_to_predictor in_fname out_fname =
  match Sys.file_exists in_fname with
  | `No | `Unknown -> failwith ("Source constraints faile " ^ out_fname ^ "does not exist")
  | `Yes -> begin
      print_endline ("generating predictor code in " ^
                     out_fname ^ " based on constraints in " ^
                     in_fname);
      let constraints = In_channel.read_all in_fname in
      let branches = Import.parse_branches constraints in
      let predictor = gen_predictor branches in
      Out_channel.write_all out_fname ~data:predictor
    end

let () =
  let fname = Sys.argv.(1) in
  let out_fname = fname ^ ".py" in
  convert_constraints_to_predictor fname out_fname
