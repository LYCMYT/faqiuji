import hashlib
import tempfile
import unittest
from pathlib import Path
from engineering.evidence_schema import validate_components

class EvidenceInputs(unittest.TestCase):
    def test_real_link_identity_coverage_and_numeric_contract(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'record.csv';p.write_text('synthetic test fixture only')
            row=dict(instance_id='A',mass_kg=2.,com_world_mm=[0.,0.,1.],source='E1',hardware_revision='TEST',pose={'height':0,'yaw':0,'pitch':0})
            index=dict(root=td,hardware_revision='TEST',pose={'height':0,'yaw':0,'pitch':0},records={'E1':dict(path='record.csv',sha256=hashlib.sha256(p.read_bytes()).hexdigest(),bytes=p.stat().st_size,instance_id='A',hardware_revision='TEST',pose={'height':0,'yaw':0,'pitch':0})})
            validate_components([row],{'A'},index)
            with self.assertRaises(ValueError):validate_components([{**row,'pose':{'height':False,'yaw':0,'pitch':0}}],{'A'},index)
            wrong_index={**index,'records':{'E1':{**index['records']['E1'],'pose':{'height':0,'yaw':False,'pitch':0}}}}
            with self.assertRaises(ValueError):validate_components([row],{'A'},wrong_index)
            for badrow,badindex in [({**row,'source':''},{**index,'records':{'':index['records']['E1']}}),({**row,'pose':{}},{**index,'pose':{},'records':{'E1':{**index['records']['E1'],'pose':{}}}})]:
                with self.assertRaises(ValueError):validate_components([badrow],{'A'},badindex)
            for rows,expected in [([row,row],{'A'}),([row],{'A','B'}),([{**row,'mass_kg':True}],{'A'}),([{**row,'com_world_mm':[False,0,1]}],{'A'}),([{**row,'source':None}],{'A'}),([{**row,'pose':{'height':1}}],{'A'}),([{**row,'hardware_revision':'wrong'}],{'A'})]:
                with self.assertRaises(ValueError):validate_components(rows,expected,index)
            p.write_text('changed')
            with self.assertRaises(ValueError):validate_components([row],{'A'},index)
            p.write_text('');index['records']['E1'].update(bytes=0,sha256=hashlib.sha256(b'').hexdigest())
            with self.assertRaises(ValueError):validate_components([row],{'A'},index)

if __name__=='__main__':unittest.main()
