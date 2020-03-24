open Core
open Ir

let rewrite (t:term) : term option =
  match t with
  (* user_buf[12:27] -> pkt.ether.type *)
  | Utility (Slice ({v=Id "user_buf";t=_}, 12, 16)) ->
    Some (Str_idx ({v=Str_idx ({v=Id "pkt";t=Unknown}, "ether");t=Unknown},
                   "type"))
  (* buf_value[32:63] -> mbuf.packet_type *)
  | Utility (Slice ({v=Id "buf_value";t=_}, 32, 32)) ->
    Some (Str_idx ({v=Id "mbuf";t=Unknown}, "packet_type"))
  | _ -> None
