#!/usr/bin/env python3
"""Read-only BM1 nominal shuttle support probe; not dynamics or a CAD patch.

Usage:
  python reproduce_support_findings.py --repo /absolute/path/to/faqiuji \
      --output /tmp/bm1-support-results.json

Requires the project's CadQuery environment. Imports the inspected repository,
builds its nominal R3 fixture in memory and writes only the requested result
outside that repository. Bytecode writes are disabled. Original evidence in
support_evidence.json was produced at c8c52514 on CadQuery 2.7 / OCCT 7.8.
Future revisions can change or remove this finding; this is not a release gate.
"""
import argparse
import json
import math
from pathlib import Path
import subprocess
import sys

sys.dont_write_bytecode = True


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    root = args.repo.resolve()
    output = args.output.resolve()
    if output.is_relative_to(root):
        parser.error('Audit output must be outside the inspected repository')
    sys.path.insert(0, str(root))

    from cad.assemblies.r3_fixture import model, posed
    from cad.parts.recipe import build
    from cad.assemblies.kinematics import parameters
    from cad.export_all import exact_bbox
    from tools.check_collisions import bbox, overlaps
    import cadquery as cq

    rows, variants, spec, base = model()
    data = json.loads((root / 'data/geometry.json').read_text(encoding='utf-8'))
    env = parameters()
    cork = build(next(x['shape'] for x in data['instances']
                      if x['instance_id'] == 'PRT-REF-CORK'), env)
    skirt = build(next(x['shape'] for x in data['instances']
                       if x['instance_id'] == 'PRT-REF-SKIRT'), env)
    bottom = cq.Workplane('XY').add(cork).faces('<Z').val()
    revision = subprocess.run(['git', '-C', str(root), 'rev-parse', 'HEAD'],
                              check=True, capture_output=True, text=True).stdout.strip()
    report = dict(read_only=True, revision=revision, cadquery_version=cq.__version__,
                  assumptions='Nominal CAD reference cork/skirt; no measured mass, friction or impact model.',
                  cork_axis_x=env['load_x'], cork_axis_y=0,
                  cork_bottom_z=env['cork_z_min'], cases=[])
    for clamp in (14, 0):
        state = {**base['state'], 'guide': 0, 'upper': 0, 'gate': 85, 'clamp': clamp}
        entries = []
        for row, shape in posed(rows, state):
            distance = cork.distance(shape)
            if distance < 20:
                contact = bottom.intersect(shape)
                contact_box = None
                if contact.Area() > 1e-8:
                    box = exact_bbox(contact)
                    contact_box = [box.xmin, box.ymin, box.zmin, box.xmax, box.ymax, box.zmax]
                entries.append(dict(instance=row['instance_id'], distance_mm=distance,
                                    bottom_contact_area_mm2=contact.Area(),
                                    bottom_contact_bbox=contact_box,
                                    overlap_mm3=cork.intersect(shape).Volume()))
        report['cases'].append(dict(clamp_mm=clamp,
                                   nearby_cork_bodies=sorted(entries, key=lambda x: x['distance_mm'])))

    # Fixed reviewed edge, not inferred for a redesigned cradle. Rotate full
    # reference cork and skirt together; collision-free perturbation is not a
    # prediction of the real shuttle's eventual dynamic resting position.
    pivot_x = env['load_x'] + 5.5
    pivot_z = env['cork_z_min']
    report['reviewed_pivot'] = [pivot_x, 0, pivot_z]
    shapes = posed(rows, {**base['state'], 'guide': 0, 'gate': 85})
    report['tip_probe'] = []
    for degrees in (0.01, 0.1, 0.25, 0.5, 1, 2, 3):
        cork_rotated = cork.rotate((pivot_x, 0, pivot_z), (pivot_x, 1, pivot_z), -degrees)
        skirt_rotated = skirt.rotate((pivot_x, 0, pivot_z), (pivot_x, 1, pivot_z), -degrees)
        hits = []
        for row, shape in shapes:
            for label, reference in (('cork', cork_rotated), ('skirt', skirt_rotated)):
                if overlaps(bbox(reference), bbox(shape)):
                    volume = reference.intersect(shape).Volume()
                    if volume > .01:
                        hits.append(dict(body=row['instance_id'], reference=label, volume_mm3=volume))
        report['tip_probe'].append(dict(deg=degrees, hits=hits,
                                        cork_center=cork_rotated.Center().toTuple()))
    radius, offset = 13.25, 5.5
    report['reviewed_analytic_cap_area_mm2'] = (
        radius * radius * math.acos(offset / radius)
        - offset * math.sqrt(radius * radius - offset * offset)
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'revision': revision, 'output': str(output),
                      'fixture_instances': len(rows), 'cases': len(report['cases'])}))


if __name__ == '__main__':
    main()
