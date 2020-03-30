open Core
open Ir

let rewrite_rules : (term -> term option) list =
  [(function (* Stage #1 rewriting *)
      (* user_buf[12:27] -> pkt.ether.type *)
      | Utility (Slice ({v=Id "user_buf";t=_}, 96, 16)) ->
        Some (Str_idx ({v=Str_idx ({v=Id "pkt";t=Unknown}, "ether");t=Unknown},
                       "type"))
      (* buf_value[32:63] -> mbuf.packet_type *)
      | Utility (Slice ({v=Id "buf_value";t=_}, 256, 32)) ->
        Some (Str_idx ({v=Id "mbuf";t=Unknown}, "packet_type"))
      | _ -> None);
   (function (* Stage #2 rewriting *)
     | Bop (Eq, {v=Int i; t}, x) -> Some (Bop (Eq, x, {v=Int i; t}))
     | _ -> None);
  ]
