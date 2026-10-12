"""Fingerprint a game project that is not a web build: Unity, Godot, Unreal, GameMaker, Defold, Cocos, native
C/C++/Rust/C#, Android and iOS. `wise scan <folder>` picks this module when it finds one of their marker files.

Every reader below looks at project files only (settings, manifests, build scripts) and never runs the engine.
A fact that is not in those files is reported as not found; nothing is guessed. Folder sizes come from one walk
that skips each engine's caches (Library/, .godot/, Intermediate/, target/ ...).
"""
from __future__ import annotations

import json
import os
import re
from pathlib import Path

MAX_ENTRIES = 60_000
MAX_DEPTH = 9
MAX_TEXT = 2_000_000
AUDIO_EXT = (".mp3", ".ogg", ".oga", ".wav", ".m4a", ".aac", ".opus", ".flac", ".aif", ".aiff", ".wma", ".xm", ".mod",
             ".it", ".s3m", ".mid", ".midi", ".bank", ".fsb", ".wem", ".bnk")
VIDEO_EXT = (".mp4", ".mov", ".webm", ".mkv", ".m4v", ".avi")
# caches, builds and vendored trees: never part of what a person edits, and often huge
SKIP_DIRS = {".git", ".hg", ".svn", "node_modules", "__pycache__", ".venv", "venv", ".idea", ".vs", ".vscode", ".gradle",
             "Library", "Temp", "Obj", "obj", "Logs", "UserSettings", "MemoryCaptures", "Recordings",        # Unity
             ".godot", ".import", ".mono",                                                                     # Godot
             "Intermediate", "Saved", "DerivedDataCache", "Binaries",                                          # Unreal
             "target", "build", "Build", "Builds", "cmake-build-debug", "cmake-build-release", "out", "bin", "dist",
             "Pods", "DerivedData", ".build", "xcuserdata", ".cxx", ".externalNativeBuild"}
LANGS = {".cs": "C#", ".gd": "GDScript", ".cpp": "C++", ".cc": "C++", ".cxx": "C++", ".hpp": "C++", ".h": "C/C++ header",
         ".c": "C", ".rs": "Rust", ".lua": "Lua", ".script": "Lua (Defold)", ".gui_script": "Lua (Defold)", ".gml": "GML",
         ".kt": "Kotlin", ".java": "Java", ".swift": "Swift", ".m": "Objective-C", ".mm": "Objective-C++",
         ".ts": "TypeScript", ".js": "JavaScript", ".py": "Python", ".shader": "shader", ".gdshader": "shader",
         ".hlsl": "shader", ".glsl": "shader", ".usf": "shader"}


def human(n: int | None) -> str:
    if n is None:
        return "?"
    for unit, size in (("GB", 1 << 30), ("MB", 1 << 20), ("kB", 1 << 10)):
        if n >= size:
            return f"{n / size:.1f} {unit}"
    return f"{n} B"


class Tree:
    """One capped walk of the project: every file's size, by relative posix path."""

    def __init__(self, root: Path):
        self.root, self.files, self.truncated = root, {}, False
        for dirpath, dirs, names in os.walk(root):
            rel = Path(dirpath).relative_to(root)
            depth = len(rel.parts)
            dirs[:] = sorted(d for d in dirs if d not in SKIP_DIRS and not d.endswith((".xcodeproj", ".xcworkspace"))
                             and depth < MAX_DEPTH)
            for n in names:
                if len(self.files) >= MAX_ENTRIES:
                    self.truncated = True
                    return
                p = Path(dirpath) / n
                try:
                    self.files[(rel / n).as_posix()] = p.stat().st_size
                except OSError:
                    pass

    def glob(self, *suffixes: str, under: str = "") -> list[str]:
        pre = under.rstrip("/") + "/" if under else ""
        return [f for f in self.files if f.startswith(pre) and f.lower().endswith(suffixes)]

    def has(self, rel: str) -> bool:
        return rel in self.files

    def text(self, rel: str) -> str:
        try:
            with open(self.root / rel, "rb") as fh:
                return fh.read(MAX_TEXT).decode("utf-8", "replace")
        except OSError:
            return ""

    def top(self, pattern: str) -> list[str]:
        """Files at the project root whose name matches a suffix such as '.uproject'."""
        return sorted(f for f in self.files if "/" not in f and f.lower().endswith(pattern))

    def folders(self, under: str = "", limit: int = 12) -> list[dict]:
        """Direct sub-folders of `under` with their file count and size, biggest first."""
        pre = under.rstrip("/") + "/" if under else ""
        acc: dict[str, list[int]] = {}
        for f, size in self.files.items():
            if not f.startswith(pre):
                continue
            rest = f[len(pre):]
            if "/" not in rest:
                continue
            a = acc.setdefault(pre + rest.split("/", 1)[0], [0, 0])
            a[0] += 1
            a[1] += size
        rows = [dict(path=k, files=v[0], bytes=v[1]) for k, v in acc.items()]
        return sorted(rows, key=lambda r: -r["bytes"])[:limit]

    def audio(self, largest: int = 5) -> dict:
        rows = [(f, s) for f, s in self.files.items() if f.lower().endswith(AUDIO_EXT)]
        by_folder: dict[str, list[int]] = {}
        for f, s in rows:
            a = by_folder.setdefault(f.rsplit("/", 1)[0] if "/" in f else ".", [0, 0])
            a[0] += 1
            a[1] += s
        return dict(found=bool(rows), files=len(rows), bytes=sum(s for _, s in rows),
                    folders=sorted((dict(path=k, files=v[0], bytes=v[1]) for k, v in by_folder.items()), key=lambda r: -r["bytes"])[:6],
                    largest=[dict(file=f, bytes=s) for f, s in sorted(rows, key=lambda r: -r[1])[:largest]])

    def languages(self) -> list[dict]:
        acc: dict[str, list[int]] = {}
        for f, s in self.files.items():
            lang = LANGS.get(os.path.splitext(f)[1].lower())
            if lang:
                a = acc.setdefault(lang, [0, 0])
                a[0] += 1
                a[1] += s
        return sorted((dict(language=k, files=v[0], bytes=v[1]) for k, v in acc.items()), key=lambda r: -r["files"])


def _json(text: str):
    try:
        return json.loads(text)
    except (json.JSONDecodeError, ValueError):
        # GameMaker and some Unreal files carry trailing commas
        try:
            return json.loads(re.sub(r",(\s*[}\]])", r"\1", text))
        except (json.JSONDecodeError, ValueError):
            return None


def _ini(text: str) -> dict[str, dict[str, str]]:
    """A forgiving INI reader (Godot, Defold, Unreal configs repeat keys and skip quoting rules)."""
    out: dict[str, dict[str, str]] = {}
    section = ""
    for line in text.splitlines():
        line = line.strip()
        if not line or line[0] in ";#":
            continue
        m = re.match(r"\[(.+)\]$", line)
        if m:
            section = m.group(1).strip()
            continue
        if "=" in line:
            k, v = line.split("=", 1)
            out.setdefault(section, {}).setdefault(k.strip().lstrip("+"), v.strip())
    return out


def _unq(s: str | None) -> str | None:
    return s.strip().strip('"') if s else None


def _first(pattern: str, text: str, flags=0) -> str | None:
    m = re.search(pattern, text, flags)
    return m.group(1).strip() if m else None


def _audio_route(audio: dict) -> list[dict]:
    if not audio["found"]:
        return []
    f = audio["largest"][0]["file"]
    if f.lower().endswith((".bank", ".fsb", ".wem", ".bnk", ".xm", ".mod", ".it", ".s3m", ".mid", ".midi")):
        return []
    return [dict(do=f'wise music-enhance "{f}" --check --for music',
                 why=f"{audio['files']} audio files ({human(audio['bytes'])}): measure the biggest one against a target without playing it")]


CLIP_ROUTE = dict(do="record a short gameplay clip, then: wise scan clip.mp4 --sheet",
                  why="duration, cuts, loudness and a contact sheet of what the game looks like in motion")


# --------------------------------------------------------------------------- Unity

UNITY_PACKAGES = {"com.unity.render-pipelines.universal": "URP", "com.unity.render-pipelines.high-definition": "HDRP",
                  "com.unity.inputsystem": "Input System", "com.unity.addressables": "Addressables", "com.unity.textmeshpro": "TextMeshPro",
                  "com.unity.cinemachine": "Cinemachine", "com.unity.netcode.gameobjects": "Netcode for GameObjects",
                  "com.unity.entities": "Entities (DOTS)", "com.unity.test-framework": "Test Framework", "com.unity.timeline": "Timeline",
                  "com.unity.ugui": "uGUI", "com.unity.2d.sprite": "2D Sprite", "com.unity.2d.tilemap": "2D Tilemap",
                  "com.unity.ads": "Unity Ads", "com.unity.purchasing": "In-App Purchasing", "com.unity.services.analytics": "Unity Analytics"}


def unity(t: Tree) -> dict | None:
    ver_txt = t.text("ProjectSettings/ProjectVersion.txt")
    scenes_all = t.glob(".unity")
    if not ver_txt and not t.has("Packages/manifest.json") and not (scenes_all and t.glob(".meta", under="Assets")):
        return None
    evidence = [f for f in ("ProjectSettings/ProjectVersion.txt", "Packages/manifest.json") if t.has(f)]
    if scenes_all:
        evidence.append(f"{len(scenes_all)} .unity scene{'s' if len(scenes_all) != 1 else ''}")
    version = _first(r"m_EditorVersion:\s*(\S+)", ver_txt)
    manifest = _json(t.text("Packages/manifest.json")) or {}
    deps = manifest.get("dependencies") or {}
    packages = [dict(name=k, label=UNITY_PACKAGES[k], version=str(v)) for k, v in deps.items() if k in UNITY_PACKAGES]
    pipeline = next((p["label"] for p in packages if p["label"] in ("URP", "HDRP")), "built-in (no SRP package)" if deps else None)
    settings = t.text("ProjectSettings/ProjectSettings.asset")
    build = t.text("ProjectSettings/EditorBuildSettings.asset")
    in_build = [dict(file=m.group(2).strip(), enabled=m.group(1) == "1")
                for m in re.finditer(r"-\s*enabled:\s*(\d)\s*\n\s*path:\s*(.+)", build)]
    entries = [dict(file=s["file"], why="scene in the build list" + ("" if s["enabled"] else " (disabled)")) for s in in_build[:8]]
    if not entries:
        entries = [dict(file=f, why="scene (no build list found)") for f in sorted(scenes_all)[:8]]
    ids = re.search(r"applicationIdentifier:\s*\n((?:\s{4,}\S+:.*\n)+)", settings)
    targets = [dict(platform=k.strip(), id=v.strip()) for k, v in
               (ln.split(":", 1) for ln in (ids.group(1).splitlines() if ids else []) if ":" in ln)]
    hints = [(d, p) for d, p in (("Assets/Plugins/Android", "Android"), ("Assets/Plugins/iOS", "iOS"),
                                 ("Assets/WebGLTemplates", "WebGL"), ("Assets/StreamingAssets", None)) if t.glob("", under=d)]
    for _, plat in hints:
        if plat and not any(x["platform"].lower() in (plat.lower(), "iphone" if plat == "iOS" else "") for x in targets):
            targets.append(dict(platform=plat, id=None, hint="plugin or template folder"))
    scripts = t.glob(".cs", under="Assets")
    tests = [f for f in scripts if "/Tests/" in f or "/Editor/Tests/" in f or f.endswith(("Tests.cs", "Test.cs"))]
    audio = t.audio()
    routes = []
    routes.append(dict(do=f"open the folder in Unity {version or '(version not found)'} through Unity Hub",
                       why="the editor version the project was last saved with" if version else "ProjectVersion.txt is missing"))
    routes.append(dict(do="Unity -batchmode -quit -projectPath . -buildTarget <target> -executeMethod <YourBuild.Method> -logFile -",
                       why="a headless build; the method is a static editor script you add under Assets/Editor"))
    if tests or "com.unity.test-framework" in deps:
        routes.append(dict(do="Unity -batchmode -projectPath . -runTests -testPlatform EditMode -testResults results.xml -logFile -",
                           why=f"{len(tests)} test script{'s' if len(tests) != 1 else ''} found" if tests else "the Test Framework package is installed"))
    routes += _audio_route(audio) + [CLIP_ROUTE]
    return dict(key="unity", label="Unity", version=version, evidence=evidence,
                details=dict(product=_first(r"productName:\s*(.+)", settings), company=_first(r"companyName:\s*(.+)", settings),
                             bundle_version=_first(r"bundleVersion:\s*(.+)", settings), render_pipeline=pipeline,
                             packages=packages, package_count=len(deps), scripts=len(scripts), scenes=len(scenes_all)),
                entries=entries, build_targets=targets, asset_root="Assets", audio=audio, routes=routes)


# --------------------------------------------------------------------------- Godot

def godot(t: Tree) -> dict | None:
    if not t.has("project.godot"):
        return None
    raw = t.text("project.godot")
    ini = _ini(raw)
    app = ini.get("application", {})
    cfg = _first(r"^config_version\s*=\s*(\d+)", raw, re.M)
    feats = re.findall(r'"([^"]+)"', app.get("config/features", ""))
    version = next((f for f in feats if re.fullmatch(r"\d+\.\d+(\.\d+)?", f)), None)
    major = {"5": "4.x", "4": "3.x", "3": "3.0"}.get(cfg or "")
    renderer = next((f for f in feats if f in ("Forward Plus", "Mobile", "GL Compatibility")), None) or \
        _unq(ini.get("rendering", {}).get("renderer/rendering_method"))
    main = _unq(app.get("run/main_scene"))
    entries = [dict(file=main.replace("res://", ""), why="run/main_scene")] if main else []
    for name, target in list(ini.get("autoload", {}).items())[:8]:
        entries.append(dict(file=_unq(target).lstrip("*").replace("res://", ""), why=f"autoload {name}"))
    presets = _ini(t.text("export_presets.cfg"))
    targets = [dict(platform=_unq(v.get("platform")), preset=_unq(v.get("name")), path=_unq(v.get("export_path")) or None)
               for k, v in presets.items() if re.fullmatch(r"preset\.\d+", k)]
    csharp = bool(t.top(".csproj") or t.top(".sln"))
    addons = sorted({f.split("/")[1] for f in t.files if f.startswith("addons/") and f.count("/") >= 2})
    audio = t.audio()
    routes = [dict(do="godot --path .", why="runs the main scene" if main else "no main scene is set: the editor will ask for one")]
    if targets:
        p = targets[0]
        routes.append(dict(do=f'godot --headless --path . --export-release "{p["preset"]}" <output file>',
                           why=f"{len(targets)} export preset{'s' if len(targets) != 1 else ''}: {', '.join(str(x['preset']) for x in targets[:5])}"))
    else:
        routes.append(dict(do="add an export preset in Project > Export (it writes export_presets.cfg)", why="no export_presets.cfg: no build target is set up"))
    if "gut" in addons:
        routes.append(dict(do="godot --headless --path . -s addons/gut/gut_cmdln.gd", why="the GUT test addon is installed"))
    routes += _audio_route(audio) + [CLIP_ROUTE]
    return dict(key="godot", label="Godot", version=version or major, evidence=["project.godot" + (f" (config_version {cfg})" if cfg else "")],
                details=dict(name=_unq(app.get("config/name")), renderer=renderer, config_version=cfg, language="C# + GDScript" if csharp else "GDScript",
                             scripts=len(t.glob(".gd")) + (len(t.glob(".cs")) if csharp else 0), scenes=len(t.glob(".tscn", ".scn")), addons=addons[:12]),
                entries=entries, build_targets=targets, asset_root="", audio=audio, routes=routes)


# --------------------------------------------------------------------------- Unreal

def unreal(t: Tree) -> dict | None:
    up = t.top(".uproject")
    if not up:
        return None
    d = _json(t.text(up[0])) or {}
    name = up[0].rsplit(".", 1)[0]
    engine_ini, game_ini = _ini(t.text("Config/DefaultEngine.ini")), _ini(t.text("Config/DefaultGame.ini"))
    maps = engine_ini.get("/Script/EngineSettings.GameMapsSettings", {})
    entries = [dict(file=maps[k], why=k) for k in ("GameDefaultMap", "EditorStartupMap", "GlobalDefaultGameMode") if maps.get(k)]
    modules = [dict(name=m.get("Name"), type=m.get("Type")) for m in d.get("Modules") or []]
    entries += [dict(file=f"Source/{m['name']}", why=f"{m['type']} module") for m in modules[:4] if m["name"]]
    target_files = sorted(f for f in t.glob(".target.cs", under="Source"))
    platforms = d.get("TargetPlatforms") or []
    targets = [dict(target=Path(f).name[:-len(".Target.cs")], file=f) for f in target_files]
    plugins = [p.get("Name") for p in d.get("Plugins") or [] if p.get("Enabled")]
    settings = game_ini.get("/Script/EngineSettings.GeneralProjectSettings", {})
    audio = t.audio()
    assoc = d.get("EngineAssociation") or None
    routes = [dict(do=f"open {up[0]} with Unreal Engine {assoc or '(association not found)'}",
                   why="EngineAssociation in the .uproject" if assoc else "the .uproject names no engine version")]
    routes.append(dict(do=f'RunUAT BuildCookRun -project="<full path>/{up[0]}" -platform=<Win64|Mac|Linux|Android|IOS> -clientconfig=Development -build -cook -stage -pak',
                       why="a headless build, cook and package (RunUAT is in Engine/Build/BatchFiles)"))
    if not modules:
        routes.append(dict(do="nothing to compile: this is a Blueprint-only project", why="the .uproject lists no code modules"))
    routes += _audio_route(audio) + [CLIP_ROUTE]
    return dict(key="unreal", label="Unreal Engine", version=assoc, evidence=[up[0]] + (["Config/DefaultEngine.ini"] if engine_ini else []),
                details=dict(name=settings.get("ProjectName") or name, project_version=settings.get("ProjectVersion"), modules=modules,
                             plugins=plugins[:20], platforms=platforms, maps=len(t.glob(".umap", under="Content")),
                             assets=len(t.glob(".uasset", under="Content")), code="C++" if modules else "Blueprint only"),
                entries=entries, build_targets=targets + [dict(platform=p) for p in platforms], asset_root="Content", audio=audio, routes=routes)


# --------------------------------------------------------------------------- GameMaker

def gamemaker(t: Tree) -> dict | None:
    yyp, gmx = t.top(".yyp"), t.top(".project.gmx")
    if not yyp and not gmx:
        return None
    if not yyp:
        return dict(key="gamemaker", label="GameMaker Studio 1", version="1.x", evidence=[gmx[0]], details=dict(name=gmx[0].split(".")[0]),
                    entries=[], build_targets=[], asset_root="", audio=t.audio(),
                    routes=[dict(do="import the .project.gmx into current GameMaker", why="GameMaker Studio 1 projects no longer build as they are"), CLIP_ROUTE])
    raw = t.text(yyp[0])
    d = _json(raw) or {}
    version = (d.get("MetaData") or {}).get("IDEVersion") or _first(r'"IDEVersion"\s*:\s*"([^"]+)"', raw)
    rooms = [((n.get("roomId") or {}).get("path")) for n in d.get("RoomOrderNodes") or []]
    entries = [dict(file=rooms[0], why="first room in the room order")] if rooms and rooms[0] else []
    targets = [dict(platform=f["path"].split("/", 1)[1]) for f in t.folders("options") if f["path"] != "options/main"]
    counts = {k: len({f.split("/")[1] for f in t.files if f.startswith(k + "/") and f.count("/") >= 2})
              for k in ("rooms", "objects", "sprites", "scripts", "sounds", "shaders", "extensions")}
    audio = t.audio()
    routes = [dict(do=f"open {yyp[0]} in GameMaker {version or '(IDE version not found)'}", why="the IDE version that last saved the project"),
              dict(do="build from the IDE, or with the command-line tool Igor from the installed runtime", why="GameMaker has no project-local build script")]
    routes += _audio_route(audio) + [CLIP_ROUTE]
    return dict(key="gamemaker", label="GameMaker", version=version, evidence=[yyp[0]],
                details=dict(name=d.get("name") or yyp[0][:-4], resources=counts), entries=entries, build_targets=targets,
                asset_root="", audio=audio, routes=routes)


# --------------------------------------------------------------------------- Defold

def defold(t: Tree) -> dict | None:
    if not t.has("game.project"):
        return None
    ini = _ini(t.text("game.project"))
    project, boot, display = ini.get("project", {}), ini.get("bootstrap", {}), ini.get("display", {})
    main = boot.get("main_collection")
    entries = [dict(file=re.sub(r"\.collectionc$", ".collection", main).lstrip("/"), why="bootstrap main_collection")] if main else []
    ids = (("android", "package", "Android"), ("ios", "bundle_identifier", "iOS"), ("osx", "bundle_identifier", "macOS"),
           ("html5", None, "HTML5"), ("windows", None, "Windows"), ("linux", None, "Linux"))
    targets = [dict(platform=label, id=ini[sec].get(key) if key else None) for sec, key, label in ids if sec in ini]
    deps = [v for k, v in project.items() if k.startswith("dependencies")]
    audio = t.audio()
    routes = [dict(do="java -jar bob.jar --archive --platform js-web resolve distclean build bundle",
                   why="a headless HTML5 build with Defold's bob.jar (swap the platform for armv7-android, arm64-ios, x86_64-win32 ...)"),
              dict(do="open game.project in the Defold editor", why="it runs and bundles from there")]
    routes += _audio_route(audio) + [CLIP_ROUTE]
    return dict(key="defold", label="Defold", version=None, evidence=["game.project"],
                details=dict(name=project.get("title"), project_version=project.get("version"),
                             display=f"{display.get('width')}x{display.get('height')}" if display.get("width") else None,
                             dependencies=deps[:10], scripts=len(t.glob(".script", ".gui_script", ".lua")),
                             note="the engine version is the editor's own; the project does not record it"),
                entries=entries, build_targets=targets, asset_root="", audio=audio, routes=routes)


# --------------------------------------------------------------------------- Cocos

def cocos(t: Tree) -> dict | None:
    pkg = _json(t.text("package.json")) or {}
    old = _json(t.text("project.json")) or {}
    x = _json(t.text(".cocos-project.json")) or {}
    creator = pkg.get("creator") or {}
    audio = t.audio()
    if isinstance(creator, dict) and creator.get("version") or (old.get("engine") or "").startswith("cocos"):
        version = creator.get("version") or old.get("version")
        scenes = sorted(t.glob(".scene", ".fire", under="assets"))
        builder = _json(t.text("settings/v2/packages/builder.json")) or _json(t.text("settings/builder.json")) or {}
        plats = sorted(k for k in (builder.get("common") or builder).keys() if k in
                       ("web-mobile", "web-desktop", "android", "ios", "mac", "windows", "wechatgame", "bytedance-mini-game", "native"))
        built = [f["path"].split("/", 1)[1] for f in Tree(t.root / "build").folders("")] if (t.root / "build").is_dir() else []
        targets = [dict(platform=p) for p in (plats or built)]
        routes = [dict(do=f"open the folder in Cocos Creator {version or '(version not found)'} through Cocos Dashboard", why="the editor version the project names"),
                  dict(do='CocosCreator --project . --build "platform=web-mobile;debug=false"', why="a headless build with the editor binary"),
                  dict(do="after a web build: wise scan build/web-mobile and wise qa <its URL>", why="a built Cocos web game scans and tests like any other web game")]
        routes += _audio_route(audio) + [CLIP_ROUTE]
        return dict(key="cocos-creator", label="Cocos Creator", version=version,
                    evidence=["package.json (creator.version)" if creator else "project.json (engine)"],
                    details=dict(name=pkg.get("name") or old.get("name"), scripts=len(t.glob(".ts", ".js", under="assets")), scenes=len(scenes)),
                    entries=[dict(file=s, why="scene") for s in scenes[:6]], build_targets=targets, asset_root="assets", audio=audio, routes=routes)
    if x or any(f.startswith("cocos2d/") for f in t.files):
        proj = {"proj.android": "Android", "proj.android-studio": "Android", "proj.ios_mac": "iOS and macOS", "proj.win32": "Windows",
                "proj.linux": "Linux", "frameworks/runtime-src/proj.android": "Android", "frameworks/runtime-src/proj.ios_mac": "iOS and macOS"}
        targets = [dict(platform=label, path=d) for d, label in proj.items() if t.glob("", under=d)]
        kind = x.get("project_type")
        entry = next((f for f in ("Classes/AppDelegate.cpp", "src/main.lua", "main.js", "src/app.js") if t.has(f)), None)
        return dict(key="cocos2d-x", label="Cocos2d-x", version=(x.get("engine_version") or "").replace("cocos2d-x-", "") or None,
                    evidence=[".cocos-project.json" if x else "cocos2d/ folder"],
                    details=dict(language={"cpp": "C++", "lua": "Lua", "js": "JavaScript"}.get(kind, kind)),
                    entries=[dict(file=entry, why="application entry")] if entry else [], build_targets=targets,
                    asset_root="Resources" if t.glob("", under="Resources") else "res", audio=audio,
                    routes=[dict(do="cocos compile -p <android|ios|mac|win32|linux> -m release", why="the cocos command-line tool builds each proj.* folder")]
                    + _audio_route(audio) + [CLIP_ROUTE])
    return None


# --------------------------------------------------------------------------- Android, iOS

GRADLE_LIBS = [("libGDX", r"com\.badlogicgames\.gdx"), ("Google Play Games", r"play-services-games|games-v2"),
               ("Unity export", r"unityLibrary"), ("AndEngine", r"andengine"), ("Oboe audio", r"com\.google\.oboe"),
               ("AdMob", r"play-services-ads"), ("Firebase", r"com\.google\.firebase"), ("Play Billing", r"com\.android\.billingclient")]


def android(t: Tree) -> dict | None:
    gradles = [f for f in t.files if re.search(r"(^|/)build\.gradle(\.kts)?$", f) and f.count("/") <= 2]
    apps = [f for f in gradles if re.search(r"com\.android\.application", t.text(f))]
    if not apps:
        return None
    app = sorted(apps, key=len)[0]
    g = t.text(app)
    everything = "\n".join(t.text(f) for f in gradles) + t.text("gradle/libs.versions.toml")

    def val(name):
        return _first(rf"\b{name}\s*(?:=|\()?\s*[\"']?([\w.\-]+)[\"']?", g)
    libs = [label for label, pat in GRADLE_LIBS if re.search(pat, everything)]
    mod = app.rsplit("/", 1)[0] if "/" in app else ""
    manifest = next((f for f in t.files if f.endswith("AndroidManifest.xml") and f.startswith(mod) and "/main/" in f), None) or \
        next((f for f in t.files if f.endswith("AndroidManifest.xml")), None)
    entries = []
    if manifest:
        m = re.search(r"<activity[^>]*android:name=\"([^\"]+)\"(?:(?!</activity>).)*android\.intent\.category\.LAUNCHER", t.text(manifest), re.S)
        entries.append(dict(file=manifest, why=f"launcher activity {m.group(1)}" if m else "manifest (no launcher activity found)"))
    flavors = re.findall(r"^\s{4,8}(?:create\(\"(\w+)\"\)|(\w+))\s*\{", _first(r"productFlavors\s*\{((?:[^{}]|\{[^{}]*\})*)\}", g) or "", re.M)
    audio = t.audio()
    is_gdx = "libGDX" in libs
    routes = [dict(do="./gradlew assembleDebug" if t.has("gradlew") else "gradle assembleDebug", why=f"builds the app module ({app})"),
              dict(do="./gradlew test" if t.has("gradlew") else "gradle test", why="unit tests of every module")]
    if is_gdx:
        desk = next((f.split("/")[0] for f in gradles if f.split("/")[0] in ("lwjgl3", "desktop")), None)
        if desk:
            routes.insert(0, dict(do=f"./gradlew {desk}:run", why="libGDX desktop launcher: the fastest way to run the game"))
    routes += _audio_route(audio) + [CLIP_ROUTE]
    return dict(key="libgdx" if is_gdx else "android", label="libGDX" if is_gdx else "Android (Gradle)",
                version=_first(r"gdxVersion\s*=\s*[\"']?([\w.\-]+)", everything + t.text("gradle.properties")) if is_gdx else None,
                evidence=[f"{app} (com.android.application)"],
                details=dict(application_id=val("applicationId") or val("namespace"), version_name=val("versionName"),
                             min_sdk=val("minSdk(?:Version)?"), target_sdk=val("targetSdk(?:Version)?"), compile_sdk=val("compileSdk(?:Version)?"),
                             libraries=libs, kotlin=bool(t.glob(".kt")), native_code=bool(t.glob("", under=f"{mod}/src/main/cpp") or t.glob("", under=f"{mod}/src/main/jni"))),
                entries=entries, build_targets=[dict(platform="Android", flavor=a or b) for a, b in flavors] or [dict(platform="Android")],
                asset_root=f"{mod}/src/main/assets" if t.glob("", under=f"{mod}/src/main/assets") else ("assets" if t.glob("", under="assets") else ""),
                audio=audio, routes=routes)


APPLE_FRAMEWORKS = ("SpriteKit", "SceneKit", "GameplayKit", "GameKit", "Metal", "MetalKit", "RealityKit", "ARKit", "AVFoundation", "StoreKit")


def ios(t: Tree) -> dict | None:
    projs = sorted(p for p in t.root.glob("*.xcodeproj") if p.is_dir()) + sorted(p for p in t.root.glob("*/*.xcodeproj") if p.is_dir())
    projs = [p for p in projs if "Pods" not in p.parts]
    if not projs:
        return None
    rel = projs[0].relative_to(t.root).as_posix()
    try:
        pbx = (projs[0] / "project.pbxproj").read_text("utf-8", "replace")[:MAX_TEXT * 4]
    except OSError:
        pbx = ""

    def val(k):
        return _first(rf"\b{k} = \"?([^\";]+)\"?;", pbx)
    names = re.findall(r"/\* Begin PBXNativeTarget section \*/(.*?)/\* End PBXNativeTarget section \*/", pbx, re.S)
    targets = sorted(set(re.findall(r"^\s+name = \"?([^\";]+)\"?;", names[0], re.M))) if names else []
    sdks = sorted(set(re.findall(r"SDKROOT = \"?(\w+)\"?;", pbx)))
    swift = t.glob(".swift", ".m", ".mm")
    used = []
    for f in swift[:400]:
        for fw in re.findall(r"^\s*(?:@?import)\s+<?(\w+)", t.text(f), re.M):
            if fw in APPLE_FRAMEWORKS and fw not in used:
                used.append(fw)
    entry = next((f for f in swift if re.search(r"@main\b|@UIApplicationMain|@NSApplicationMain", t.text(f))), None) or \
        next((f for f in swift if f.endswith(("AppDelegate.swift", "AppDelegate.m", "main.m"))), None)
    audio = t.audio()
    scheme = targets[0] if targets else "<scheme>"
    routes = [dict(do=f'xcodebuild -project "{rel}" -scheme "{scheme}" -destination "generic/platform=iOS Simulator" build', why="a headless build for the simulator"),
              dict(do=f'xcodebuild -project "{rel}" -list', why="lists the schemes and configurations Xcode knows")]
    if t.has("Podfile"):
        routes.insert(0, dict(do="pod install, then build the .xcworkspace instead of the .xcodeproj", why="the project uses CocoaPods"))
    routes += _audio_route(audio) + [CLIP_ROUTE]
    return dict(key="ios", label="Xcode project" + (f" ({', '.join(used[:3])})" if used else ""), version=None, evidence=[rel],
                details=dict(bundle_id=val("PRODUCT_BUNDLE_IDENTIFIER"), marketing_version=val("MARKETING_VERSION"),
                             ios_deployment_target=val("IPHONEOS_DEPLOYMENT_TARGET"), macos_deployment_target=val("MACOSX_DEPLOYMENT_TARGET"),
                             swift_version=val("SWIFT_VERSION"), frameworks=used,
                             packages="CocoaPods" if t.has("Podfile") else ("Swift Package Manager" if "XCRemoteSwiftPackageReference" in pbx else None)),
                entries=[dict(file=entry, why="application entry")] if entry else [],
                build_targets=[dict(target=n) for n in targets] + [dict(platform=s) for s in sdks], asset_root="", audio=audio, routes=routes)


# --------------------------------------------------------------------------- native: Rust, C/C++, C#

RUST_LIBS = ["bevy", "macroquad", "ggez", "fyrox", "godot", "gdnative", "piston", "amethyst", "wgpu", "winit", "sdl2", "raylib",
             "rodio", "kira", "rapier2d", "rapier3d", "egui", "glium", "miniquad", "tetra", "comfy"]
RUST_ENGINES = ("bevy", "macroquad", "ggez", "fyrox", "godot", "gdnative", "piston", "amethyst", "tetra", "comfy")
C_LIBS = [("SDL3", r"\bSDL3\b"), ("SDL2", r"\bSDL2\b"), ("raylib", r"\braylib\b"), ("SFML", r"\bSFML\b"), ("GLFW", r"\bglfw3?\b"),
          ("OpenGL", r"\bOpenGL\b"), ("Vulkan", r"\bVulkan\b"), ("bgfx", r"\bbgfx\b"), ("Allegro", r"\ballegro\b"), ("EnTT", r"\bEnTT\b"),
          ("Box2D", r"\bbox2d\b"), ("Dear ImGui", r"\bimgui\b"), ("OpenAL", r"\bOpenAL\b"), ("FMOD", r"\bfmod\b"), ("Bullet", r"\bBullet\b"),
          ("glm", r"\bglm\b"), ("Emscripten", r"\bEMSCRIPTEN\b"), ("Ogre", r"\bOGRE\b"), ("Magnum", r"\bMagnum\b")]
CS_LIBS = [("MonoGame", r"MonoGame\.Framework"), ("FNA", r"\bFNA\b"), ("Stride", r"Stride\.Engine"), ("Raylib-cs", r"Raylib-cs"),
           ("Silk.NET", r"Silk\.NET"), ("OpenTK", r"OpenTK"), ("Godot .NET", r"Godot\.NET\.Sdk"), ("osu-framework", r"ppy\.osu\.Framework")]


def rust(t: Tree) -> dict | None:
    if not t.has("Cargo.toml"):
        return None
    raw = t.text("Cargo.toml")
    try:
        import tomllib
        d = tomllib.loads(raw)
    except Exception:      # an old Python or a broken manifest: fall back to what a regex can see
        d = {}
    pkg = d.get("package") or {}
    deps = {**(d.get("dependencies") or {}), **((d.get("workspace") or {}).get("dependencies") or {})}
    if not d:
        deps = {m: "?" for m in re.findall(r"^([\w-]+)\s*=", raw.split("[dependencies]", 1)[-1], re.M)} if "[dependencies]" in raw else {}

    def ver(v):
        return v if isinstance(v, str) else (v.get("version") if isinstance(v, dict) else None)
    libs = [dict(name=n, version=ver(deps[n])) for n in RUST_LIBS if n in deps]
    engine = next((x for x in libs if x["name"] in RUST_ENGINES), None)
    bins = [b.get("name") for b in d.get("bin") or [] if b.get("name")]
    entries = [dict(file=f, why="binary entry") for f in ("src/main.rs",) if t.has(f)] + \
        [dict(file=f, why="library root") for f in ("src/lib.rs",) if t.has(f)] + \
        [dict(file=f, why="extra binary") for f in sorted(t.glob(".rs", under="src/bin"))[:4]]
    members = (d.get("workspace") or {}).get("members") or []
    targets = [dict(target=b, kind="bin") for b in bins] or ([dict(target=pkg.get("name"), kind="bin")] if t.has("src/main.rs") and pkg.get("name") else [])
    cfg = t.text(".cargo/config.toml")
    targets += [dict(platform=p) for p in re.findall(r"\[target\.([\w\-]+)\]", cfg)]
    if "wasm-bindgen" in deps or t.has("Trunk.toml") or "wasm32" in cfg:
        targets.append(dict(platform="wasm32-unknown-unknown", hint="wasm-bindgen, Trunk or a wasm target is configured"))
    audio = t.audio()
    routes = [dict(do="cargo run --release" if t.has("src/main.rs") or bins else "cargo build --release", why="optimised build; debug builds of games are often too slow to judge"),
              dict(do="cargo test", why="unit and integration tests")]
    if engine and engine["name"] == "bevy":
        routes.append(dict(do="cargo run --features bevy/dynamic_linking", why="much faster rebuilds while iterating on a Bevy game"))
    routes += _audio_route(audio) + [CLIP_ROUTE]
    name = pkg.get("name") if isinstance(pkg.get("name"), str) else None
    version = pkg.get("version") if isinstance(pkg.get("version"), str) else None
    return dict(key="rust-" + engine["name"] if engine else "rust", label=(engine["name"].capitalize() + " (Rust)") if engine else "Rust (Cargo)",
                version=engine["version"] if engine else None, evidence=["Cargo.toml" + (f" ({engine['name']} dependency)" if engine else "")],
                details=dict(name=name, crate_version=version, edition=pkg.get("edition"), libraries=libs, workspace_members=members[:12],
                             rust_version=pkg.get("rust-version") or _first(r'channel\s*=\s*"([^"]+)"', t.text("rust-toolchain.toml"))),
                entries=entries, build_targets=targets, asset_root="assets" if t.glob("", under="assets") else "", audio=audio, routes=routes)


def dotnet(t: Tree) -> dict | None:
    slns = t.top(".sln")
    csprojs = sorted(f for f in t.files if f.endswith(".csproj") and f.count("/") <= 2)
    if not slns and not csprojs:
        return None
    texts = {f: t.text(f) for f in csprojs[:12]}
    blob = "\n".join(texts.values())
    libs = [label for label, pat in CS_LIBS if re.search(pat, blob)]
    refs = [dict(name=m.group(1), version=m.group(2)) for m in re.finditer(r'<PackageReference\s+Include="([^"]+)"\s+Version="([^"]+)"', blob)][:20]
    frameworks = sorted(set(re.findall(r"<TargetFrameworks?>([^<]+)<", blob)))
    exes = [f for f, x in texts.items() if re.search(r"<OutputType>\s*(Win)?Exe\s*<", x)]
    entries = [dict(file=f, why="executable project") for f in exes[:4]]
    prog = next((f for f in t.glob(".cs") if f.endswith(("Program.cs", "Game1.cs"))), None)
    if prog:
        entries.append(dict(file=prog, why="program entry"))
    rids = sorted(set(sum((x.split(";") for x in re.findall(r"<RuntimeIdentifiers?>([^<]+)<", blob)), [])))
    engine = next((x for x in libs if x in ("MonoGame", "FNA", "Stride", "Raylib-cs", "osu-framework")), None)
    lib_version = next((r["version"] for r in refs if engine and engine.split("-")[0].lower() in r["name"].lower()), None)
    audio = t.audio()
    routes = [dict(do=f"dotnet run --project {exes[0]}" if exes else "dotnet build", why="builds and starts the executable project" if exes else "no executable project found: build the solution"),
              dict(do="dotnet publish -c Release -r <win-x64|osx-arm64|linux-x64> --self-contained", why="a build that runs without a .NET install")]
    if re.search(r"xunit|nunit|MSTest", blob, re.I):
        routes.append(dict(do="dotnet test", why="a test framework is referenced"))
    routes += _audio_route(audio) + [CLIP_ROUTE]
    return dict(key=(engine or "dotnet").lower().replace(".", ""), label=f"{engine} (C#)" if engine else "C# / .NET", version=lib_version,
                evidence=(slns[:1] or csprojs[:1]) + ([f"{engine} package reference"] if engine else []),
                details=dict(target_frameworks=frameworks, libraries=libs, packages=refs, projects=len(csprojs)),
                entries=entries, build_targets=[dict(platform=r) for r in rids] or [dict(platform=f) for f in frameworks],
                asset_root="Content" if t.glob("", under="Content") else "", audio=audio, routes=routes)


def cmake(t: Tree) -> dict | None:
    marker = next((f for f in ("CMakeLists.txt", "meson.build", "premake5.lua", "xmake.lua", "Makefile", "makefile", "SConstruct") if t.has(f)), None)
    if not marker:
        return None
    raw = t.text(marker)
    blob = raw + "\n".join(t.text(f) for f in ("vcpkg.json", "conanfile.txt", "conanfile.py", "CMakePresets.json") if t.has(f))
    sub = [f for f in t.files if f.endswith("CMakeLists.txt") and 0 < f.count("/") <= 2][:10]
    blob += "\n".join(t.text(f) for f in sub)
    libs = [label for label, pat in C_LIBS if re.search(pat, blob, re.I if label in ("Box2D", "Dear ImGui", "FMOD", "Allegro") else 0)]
    exes = re.findall(r"add_executable\s*\(\s*([\w\-${}.]+)", blob)
    name = _first(r"\bproject\s*\(\s*([\w\-.]+)", raw)
    version = _first(r"\bproject\s*\([^)]*\bVERSION\s+([\d.]+)", raw)
    std = _first(r"CMAKE_CXX_STANDARD\s+(\d+)", blob) or _first(r"cxx_std_(\d+)", blob)
    mains = [f for f in t.glob(".cpp", ".c", ".cc", ".cxx") if Path(f).stem.lower() == "main"][:3]
    if not mains:
        mains = [f for f in t.glob(".cpp", ".c", ".cc")[:300] if re.search(r"\bint\s+main\s*\(|\bSDL_main\b|\bWinMain\b", t.text(f))][:3]
    presets = _json(t.text("CMakePresets.json")) or {}
    targets = [dict(target=e) for e in dict.fromkeys(exes)][:8] + [dict(preset=p.get("name")) for p in presets.get("configurePresets") or []][:8]
    if "Emscripten" in libs:
        targets.append(dict(platform="web (Emscripten)", hint="the build script mentions EMSCRIPTEN"))
    audio = t.audio()
    lang = "C++" if t.glob(".cpp", ".cc", ".cxx", ".hpp") else "C"
    how = {"CMakeLists.txt": ("cmake -S . -B build -DCMAKE_BUILD_TYPE=Release && cmake --build build -j", "configure and build out of tree"),
           "meson.build": ("meson setup build --buildtype=release && meson compile -C build", "configure and build out of tree"),
           "premake5.lua": ("premake5 gmake2 && make config=release", "premake generates the makefiles first"),
           "xmake.lua": ("xmake f -m release && xmake", "xmake configures and builds"),
           "SConstruct": ("scons", "the SCons build")}.get(marker, ("make", "the Makefile's default target"))
    routes = [dict(do=how[0], why=how[1])]
    if t.has("CMakeLists.txt") and re.search(r"enable_testing|add_test\s*\(", blob):
        routes.append(dict(do="ctest --test-dir build --output-on-failure", why="the build script registers tests"))
    routes += _audio_route(audio) + [CLIP_ROUTE]
    lead = next((x for x in libs if x in ("SDL3", "SDL2", "raylib", "SFML", "Allegro", "bgfx", "Ogre", "Magnum")), None)
    return dict(key="native-" + lead.lower() if lead else "native", label=f"{lead} ({lang})" if lead else f"native {lang}",
                version=None, evidence=[marker] + ([f"{lead} in the build script"] if lead else []),
                details=dict(name=name, project_version=version, language=lang, standard=std, libraries=libs, build_system=marker,
                             note="library versions come from the system or a package manager, not from the build script" if libs else None),
                entries=[dict(file=f, why="main()") for f in mains], build_targets=targets,
                asset_root=next((d for d in ("assets", "resources", "res", "data") if t.glob("", under=d)), ""), audio=audio, routes=routes)


# --------------------------------------------------------------------------- pick one

# order matters: an engine project also contains .sln, gradle or CMake files; the engine wins
READERS = (unity, godot, unreal, gamemaker, defold, cocos, rust, android, ios, dotnet, cmake)
MARKERS = ("ProjectSettings/ProjectVersion.txt", "Packages/manifest.json", "project.godot", "game.project", "Cargo.toml",
           ".cocos-project.json")


def looks_native(root: Path) -> bool:
    """Cheap test used before the web scan: is there a non-web engine or build marker at the top of the folder?"""
    if any((root / m).is_file() for m in MARKERS):
        return True
    try:
        names = [p.name for p in root.iterdir()]
    except OSError:
        return False
    low = [n.lower() for n in names]
    if any(n.endswith((".uproject", ".yyp", ".project.gmx", ".xcodeproj")) for n in low):
        return True
    web = "package.json" in low or "index.html" in low
    if "package.json" in low:
        try:
            if isinstance(json.loads((root / "package.json").read_text("utf-8", "replace")).get("creator"), dict):
                return True
        except (OSError, ValueError):
            pass
    if "project.json" in low and '"engine"' in (root / "project.json").read_text("utf-8", "replace")[:4000]:
        return True
    if web:
        return False        # a web game with a mobile wrapper or a native add-on is still scanned as a web game
    return any(n.endswith((".sln", ".csproj")) for n in low) or any(
        n in ("cmakelists.txt", "meson.build", "premake5.lua", "xmake.lua", "makefile", "sconstruct", "build.gradle",
              "build.gradle.kts", "settings.gradle", "settings.gradle.kts") for n in low)


def fingerprint(root: Path) -> dict | None:
    """The report for a non-web game project, or None when no reader recognises the folder."""
    root = root.resolve()
    t = Tree(root)
    hits = [r for r in (reader(t) for reader in READERS) if r]
    if not hits:
        return None
    main, others = hits[0], hits[1:]
    asset_root = main.pop("asset_root")
    folders = t.folders(asset_root) if asset_root else [f for f in t.folders("") if not f["path"].startswith(".")]
    videos = [dict(file=f, bytes=s) for f, s in sorted(t.files.items(), key=lambda kv: -kv[1]) if f.lower().endswith(VIDEO_EXT)][:5]
    report = dict(kind="project", name=(main["details"].get("name") or main["details"].get("product") or root.name), path=str(root),
                  engine=dict(key=main["key"], label=main["label"], version=main["version"], evidence=main["evidence"]),
                  also=[dict(key=o["key"], label=o["label"], evidence=o["evidence"]) for o in others[:3]],
                  details={k: v for k, v in main["details"].items() if v not in (None, [], {}, "")},
                  entries=main["entries"], build_targets=main["build_targets"],
                  assets=dict(root=asset_root or ".", folders=folders, total_bytes=sum(t.files.values()), total_files=len(t.files)),
                  audio=main["audio"], videos=videos, languages=t.languages()[:8],
                  files_indexed=len(t.files), index_truncated=t.truncated, routes=main["routes"])
    return report


def _kv(d: dict) -> str:
    return ", ".join(f"{k} {v}" for k, v in d.items() if v not in (None, "", [], {}))


def format_project(r: dict) -> str:
    e = r["engine"]
    lines = [f"{r['name']}  (project folder)", f"  path:       {r['path']}",
             f"  engine:     {e['label']}" + (f"  version {e['version']}" if e["version"] else "  version not found") + f"  [{e['key']}]"]
    if e["evidence"]:
        lines.append(f"              evidence: {'; '.join(e['evidence'])}")
    if r["also"]:
        lines.append("  also:       " + "; ".join(f"{o['label']} ({o['evidence'][0]})" for o in r["also"]))
    for k, v in r["details"].items():
        if isinstance(v, list):
            v = ", ".join(_kv(x) if isinstance(x, dict) else str(x) for x in v)
        elif isinstance(v, dict):
            v = _kv(v)
        lines.append(f"  {(k.replace('_', ' ') + ':'):<24}{v}")
    lines.append("  entries:    " + ("not found" if not r["entries"] else ""))
    lines += [f"    {x['file']}  ({x['why']})" for x in r["entries"]]
    lines.append("  build targets: " + ("not found" if not r["build_targets"] else "; ".join(_kv(x) for x in r["build_targets"])))
    a = r["assets"]
    lines.append(f"  files:      {a['total_files']} files, {human(a['total_bytes'])}" + ("  (index truncated)" if r["index_truncated"] else ""))
    lines.append(f"  folders under {a['root']}:")
    lines += [f"    {f['path']:<40} {f['files']:>6} files  {human(f['bytes']):>9}" for f in a["folders"]] or ["    none"]
    au = r["audio"]
    lines.append("  audio:      " + (f"{au['files']} files, {human(au['bytes'])}" if au["found"] else "not found"))
    lines += [f"    {f['path']:<40} {f['files']:>6} files  {human(f['bytes']):>9}" for f in au.get("folders", [])[:4]]
    if au["found"]:
        lines.append("    largest: " + ", ".join(f"{Path(x['file']).name} {human(x['bytes'])}" for x in au["largest"][:3]))
    if r["videos"]:
        lines.append("  videos:     " + ", ".join(f"{x['file']} {human(x['bytes'])}" for x in r["videos"]))
    if r["languages"]:
        lines.append("  code:       " + ", ".join(f"{x['language']} {x['files']}" for x in r["languages"]))
    lines.append("  what to try next:")
    lines += [f"    {n}. {rt['do']}  ({rt['why']})" for n, rt in enumerate(r["routes"], 1)]
    return "\n".join(lines)
