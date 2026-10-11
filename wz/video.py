"""wz video (stub: replaced by the real module)."""


def register(sub):
    p = sub.add_parser("video", help="(not built yet)")
    p.set_defaults(func=lambda a: print("wz video: not built yet"))
