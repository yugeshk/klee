open Core
open Ir

let rewrite_rules : (term -> term option) list =
  [(function (* Stage #1 rewriting *)
   (* Please ensure any field inside a struct is rewritten here, in particular the first field 
    * It will otherwise be overwritten bby the first rule in stage 2 *)

      (* user_buf[12:14] -> pkt.ether.type *)
      | Utility (Slice ({v=Id "user_buf";t=_}, 96, 16)) ->
        Some (Str_idx ({v=Str_idx ({v=Id "pkt";t=Unknown}, "ether");t=Unknown},
                       "type"))
      (* buf_value[32:36] -> mbuf.packet_type *)
      | Utility (Slice ({v=Id "buf_value";t=_}, 256, 32)) ->
        Some (Str_idx ({v=Id "pkt";t=Unknown}, "type"))
      (* user_buf[23:24] -> pkt.protocol *)
      | Utility (Slice ({v=Id "user_buf";t=_}, 184, 8)) ->
      Some (Str_idx ({v=Id "pkt";t=Unknown}, "protocol"))
      | _ -> None);

   (function (* Stage #2 rewriting *)
      (* Var[0:x] -> Var *)
      | Utility (Slice ({v = Id var ;t=_}, 0, _)) -> Some (Id var)
      (* Int == x -> x == Int *)
      | Bop (Eq, {v=Int i; t}, x) -> Some (Bop (Eq, x, {v=Int i; t}))
      | _ -> None);

    (function (* Stage #3 rewriting *)
      (* x == 0 -> Not x *)
      | Bop (Eq, x, {v = Int 0; t = Uint32}) -> Some (Not x)
      | _ -> None);

    (function (* Stage #4 rewriting *)
      (* Not(Not(x)) -> x *)
      | Not ({v = Not x; t=_})-> Some (x.v)
      | _ -> None);
    

   (function (* Stage #5 rewriting *)
      (* pkt.is_IP *)
      | Bop (Or, 
            {v=Bop(Eq,
                    {v=Bop(Bit_and,{v=Str_idx({v = Id "pkt"; t = Unknown}, "type"); t = Uint32}, {v = Int 16; t = Uint32});t = Uint32},
                    {v = Int 16;t = Uint32});t = Boolean},
            {v = Bop(And,
                    {v = (Not {v = Str_idx({v = Id "pkt"; t = Unknown}, "type"); t = Uint32});t = Boolean},
                    {v = Bop(Eq, {v = Str_idx({v = Str_idx({v = Id "pkt"; t = Unknown}, "ether"); t = Unknown}, "type"); t= Sint16},{v = Int 8; t = Sint16}); t = Boolean}); t = Boolean})
        -> Some (Str_idx({v = Id "pkt"; t = Unknown}, "is_IP"))

      (* pkt.is_TCP *)
      | Bop(Eq,
            {v = Str_idx({v = Id "pkt"; t = Unknown},"protocol"); t = Sint8},
            {v = Int 6; t = Sint8})
        -> Some (Str_idx({v = Id "pkt"; t = Unknown}, "is_TCP"))

      (* pkt.is_UDP *)
      | Bop(Eq,
            {v = Str_idx({v = Id "pkt"; t = Unknown},"protocol"); t = Sint8},
            {v = Int 17; t = Sint8})
        -> Some (Str_idx({v = Id "pkt"; t = Unknown}, "is_UDP"))
      | _ -> None);
  ]