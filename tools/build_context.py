"""Content-based R4 provenance; run identity is distinct from input identity."""
from dataclasses import dataclass, asdict, replace
from datetime import datetime, timezone
from pathlib import Path
import hashlib
import importlib.metadata
import json
import os
import platform
import subprocess
import uuid
import shutil
from functools import lru_cache
from tools.input_manifest import classify_paths

RULE_VERSION = 'bm1-r4-provenance-v1'


def file_hash(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def fingerprint_inputs(root: Path, relative_paths: list[str]) -> str:
    entries = [(p, file_hash(Path(root)/p)) for p in sorted(set(relative_paths))]
    return hashlib.sha256(json.dumps([RULE_VERSION, entries], ensure_ascii=False, separators=(',', ':')).encode()).hexdigest()


def code_paths(root):
    extensions={'.py','.html','.js','.css','.json','.md','.txt','.cmd','.yaml','.yml'}
    paths=[p.relative_to(root).as_posix() for folder in ('cad','control','engineering','tools','blender','tests','viewer','docs','.github')
                  for p in (root/folder).rglob('*') if p.is_file() and p.suffix in extensions
                  and '__pycache__' not in p.parts and not (folder=='tools' and 'blender' in p.relative_to(root/'tools').parts)]
    paths += [p.name for p in root.iterdir() if p.is_file() and p.suffix in {'.md','.txt','.cmd','.toml'}]
    return sorted(paths)

@lru_cache(maxsize=32)
def executable_identity(path,size,mtime):
    # Content hash, not just executable name/version, invalidates replaced runtimes.
    name=Path(path).name.lower()
    args=[path,'--version' if 'blender' in name else '-version']
    if 'chrome' in name and os.name=='nt':args=['powershell','-NoProfile','-Command',"(Get-Item -LiteralPath '"+path.replace("'","''")+"').VersionInfo.ProductVersion"]
    try:
        p=subprocess.run(args,capture_output=True,text=True,timeout=20)
        lines=(p.stdout or p.stderr).splitlines();version=lines[0] if p.returncode==0 and lines else 'NOT_RUN'
    except (OSError,subprocess.TimeoutExpired):version='NOT_RUN'
    return {'path':path,'bytes':size,'sha256':file_hash(path),'version':version}


def tool_versions():
    result = {'python': platform.python_version(), 'platform': platform.platform()}
    for package in ('cadquery','cadquery-ocp','numpy','reportlab','pillow','pymupdf','playwright'):
        try: result[package] = importlib.metadata.version(package)
        except importlib.metadata.PackageNotFoundError: result[package] = 'NOT_INSTALLED'
    for name, variable in [('blender','BM1_BLENDER_EXE'),('ffmpeg','BM1_FFMPEG_EXE'),('ffprobe','BM1_FFPROBE_EXE'),('chrome','BM1_CHROME_EXE')]:
        selected=os.environ.get(variable) or shutil.which(name)
        if not selected and name=='chrome':selected='C:/Program Files/Google/Chrome/Application/chrome.exe'
        path=Path(selected) if selected else None
        result[name]=executable_identity(str(path.resolve()),path.stat().st_size,path.stat().st_mtime_ns) if path and path.is_file() else {'status':'NOT_AVAILABLE'}
    result['environment_policy']='Measured candidate environment; no physical or approved-production qualification inferred'
    font=Path(os.environ.get('BM1_CHINESE_FONT','C:/Windows/Fonts/msyh.ttc'))
    result['chinese_font']={'path':str(font),'sha256':file_hash(font)} if font.is_file() else {'status':'NOT_AVAILABLE'}
    return result


def atomic_json(path, value):
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name+'.'+uuid.uuid4().hex+'.tmp')
    temp.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding='utf-8')
    os.replace(temp, path)


@dataclass(frozen=True)
class BuildContext:
    run_id: str
    commit_sha: str
    input_sha256: str
    code_sha256: str
    tool_versions: dict
    started_at: str
    stage: str
    scope: str

    @classmethod
    def create(cls, root, stage='build', scope='full'):
        root = Path(root)
        paths = classify_paths(root)
        git = subprocess.run(['git','-C',str(root),'rev-parse','HEAD'], capture_output=True, text=True)
        return cls(uuid.uuid4().hex, git.stdout.strip() if git.returncode == 0 else 'UNVERSIONED',
                   fingerprint_inputs(root, paths['authoritative']+paths['evidence_index']),
                   fingerprint_inputs(root, code_paths(root)), tool_versions(),
                   datetime.now(timezone.utc).isoformat(), stage, scope)

    def for_stage(self, stage, scope=None):
        return replace(self, stage=stage, scope=self.scope if scope is None else scope)

    def to_dict(self): return asdict(self)

    def assert_current(self, root):
        now = BuildContext.create(root, self.stage, self.scope)
        for field in ('input_sha256','code_sha256','tool_versions'):
            if getattr(self, field) != getattr(now, field):
                raise RuntimeError('Stale build source: '+field)

    def report(self, status, completed_checks=(), artifact_hashes=None, **values):
        return {**self.to_dict(), 'status':status, 'completed_checks':list(completed_checks),
                'artifact_hashes':artifact_hashes or {}, **values}


def active_context(root, stage, scope='full'):
    filename = os.environ.get('BM1_BUILD_CONTEXT')
    if filename:
        ctx = BuildContext(**json.loads(Path(filename).read_text(encoding='utf-8')))
        ctx.assert_current(root)
        return ctx.for_stage(stage, scope)
    return BuildContext.create(root, stage, scope)


def require_cache(root, cache_report):
    report = json.loads(Path(cache_report).read_text(encoding='utf-8'))
    ctx = BuildContext(**{k: report[k] for k in BuildContext.__dataclass_fields__})
    ctx.assert_current(root)
    for path, digest in report['artifact_hashes'].items():
        if file_hash(Path(root)/path) != digest: raise RuntimeError('Corrupt cache: '+path)
    return report
