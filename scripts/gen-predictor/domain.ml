open Core
open Ir

let rewrite (t:term) : term option =
  match t with
  (* user_buf[12:14] -> pkt.ether.type *)
  | Utility (Slice ({v=Id "user_buf";t=_}, 96, 16)) ->
    Some (Str_idx ({v=Str_idx ({v=Id "pkt";t=Unknown}, "ether");t=Unknown},
                   "type"))
  (* user_buf[23:24] -> pkt.protocol *)
  | Utility (Slice ({v=Id "user_buf";t=_}, 184, 8)) ->
    Some (Str_idx ({v=Id "pkt";t=Unknown}, "protocol"))

  (* buf_value[32:36] -> mbuf.packet_type *)
    | Utility (Slice ({v=Id "buf_value";t=_}, 256, 32)) ->
    Some (Str_idx ({v=Id "pkt";t=Unknown}, "type"))
    
  | _ -> None