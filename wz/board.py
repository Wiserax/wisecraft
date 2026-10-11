"""wz board (stub: replaced by the real module)."""


def register(sub):
    p = sub.add_parser("board", help="(not built yet)")
    p.set_defaults(func=lambda a: print("wz board: not built yet"))
