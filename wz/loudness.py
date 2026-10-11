"""wz loudness (stub: replaced by the real module)."""


def register(sub):
    p = sub.add_parser("loudness", help="(not built yet)")
    p.set_defaults(func=lambda a: print("wz loudness: not built yet"))
