"""wz publish (stub: replaced by the real module)."""


def register(sub):
    p = sub.add_parser("publish", help="(not built yet)")
    p.set_defaults(func=lambda a: print("wz publish: not built yet"))
