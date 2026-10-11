"""wz kb (stub: replaced by the real module)."""


def register(sub):
    p = sub.add_parser("kb", help="(not built yet)")
    p.set_defaults(func=lambda a: print("wz kb: not built yet"))
