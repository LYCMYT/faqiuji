"""Physical mass/COM evidence must identify actual records, hardware and pose."""
from pathlib import Path
import hashlib
import math
from numbers import Real

def finite_number(value):
    try:return isinstance(value,Real) and not isinstance(value,bool) and math.isfinite(value)
    except (OverflowError,ValueError,TypeError):return False

def validate_numeric_rows(rows, *, allow_missing=False):
    ids=[]
    for row in rows:
        identifier=row.get('instance_id')
        if not isinstance(identifier,str) or not identifier:raise ValueError('Invalid instance_id')
        if identifier in ids:raise ValueError('Duplicate instance_id: '+identifier)
        ids.append(identifier)
        mass=row.get('mass_kg');xyz=row.get('com_world_mm')
        if mass is None and allow_missing:continue
        if not finite_number(mass) or mass<=0:raise ValueError('Mass must be finite positive non-bool')
        if xyz is None and allow_missing:continue
        if not isinstance(xyz,(list,tuple)) or len(xyz)!=3 or not all(finite_number(x) for x in xyz):raise ValueError('Invalid 3D COM')
    return set(ids)

def validate_components(rows: list[dict], expected_instances: set[str], evidence_index: dict) -> list[dict]:
    ids=validate_numeric_rows(rows)
    if not expected_instances or ids!=set(expected_instances):raise ValueError('Instance coverage mismatch')
    if not evidence_index.get('hardware_revision') or not isinstance(evidence_index.get('pose'),dict):raise ValueError('Expected hardware revision and pose required')
    for row in rows:
        source=row.get('source')
        if not isinstance(source,str) or source not in evidence_index.get('records',{}):raise ValueError('Missing source record')
        entry=evidence_index['records'][source]
        for key in ('hardware_revision','pose'):
            if row.get(key)!=evidence_index[key] or entry.get(key)!=evidence_index[key]:raise ValueError('Evidence '+key+' mismatch')
        if entry.get('instance_id')!=row['instance_id']:raise ValueError('Evidence instance mismatch')
        path=Path(evidence_index.get('root','.'))/entry.get('path','')
        if not path.is_file():raise ValueError('Evidence file not available')
        raw=path.read_bytes()
        if entry.get('bytes')!=len(raw) or entry.get('sha256')!=hashlib.sha256(raw).hexdigest():raise ValueError('Evidence file fingerprint mismatch')
    return rows
