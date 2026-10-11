"""wz qa (stub: replaced by the real module)."""


def register(sub):
    p = sub.add_parser("qa", help="(not built yet)")
    p.set_defaults(func=lambda a: print("wz qa: not built yet"))
