"""wz scan (stub: replaced by the real module)."""


def register(sub):
    p = sub.add_parser("scan", help="(not built yet)")
    p.set_defaults(func=lambda a: print("wz scan: not built yet"))
