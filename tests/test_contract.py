"""Mechanical contracts, not visual snapshots."""
import unittest, sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))

class Contract(unittest.TestCase):
    def test_kinematic_module_exists(self):
        self.assertTrue((Path(__file__).resolve().parents[1]/'cad/assemblies/kinematics.py').exists(), 'kinematic model not implemented')
    def test_interlocks(self):
        from cad.assemblies.kinematics import permitted
        self.assertFalse(permitted(dict(guide=0,slide=105,yaw=0,pitch=0,clamp=0)))
        self.assertFalse(permitted(dict(guide=115,slide=0,yaw=35,pitch=55,clamp=0)))
        self.assertFalse(permitted(dict(guide=115,slide=185,yaw=0,pitch=0,clamp=0)))
        self.assertFalse(permitted(dict(guide=115,slide=185,yaw=0,pitch=0,clamp=.001)))
        self.assertTrue(permitted(dict(guide=115,slide=105,yaw=35,pitch=55,clamp=0)))
    def test_height_pitch(self):
        from cad.assemblies.kinematics import point
        import numpy as np
        p=point([100,0,0],'MOVING_HEAD',dict(height=1800,pitch=60,yaw=0))
        np.testing.assert_allclose(p,[50,0,1886.6025404],atol=1e-6)
        q=point([-190,0,650],'FIXED_HEAD_CARRIER',dict(height=1800,pitch=60,yaw=45))
        np.testing.assert_allclose(q,[-190,0,2450])
    def test_main_step_complete(self):
        import cadquery as cq,json
        r=Path(__file__).resolve().parents[1]
        rec=json.loads((r/'data/instances.json').read_text(encoding='utf-8'))
        expected=sum(x['solid_count'] for x in rec if x['part_id']=='PRT-0702')
        s=cq.importers.importStep(str(r/'output/step/parts/PRT-0702.step')).val()
        self.assertEqual(len(s.Solids()),expected)

if __name__=='__main__': unittest.main()
