import unittest
from engineering.evaluate import evaluate

class SupportSolver(unittest.TestCase):
    def test_five_support_reactivation(self):
        points=[(350,-180,1000),(90,380,3),(-440,-500,1),(-250,-300,1),(440,-320,10)]
        supports=[dict(x_mm=x,y_mm=y,vertical_stiffness_N_mm=k) for x,y,k in points]
        rows=[dict(instance_id='synthetic',mass_kg=40.,com_world_mm=[70.,-280.,1000.])]
        result=evaluate(rows,supports,allow_partial=True)
        self.assertTrue(result['support_solution_valid'])
        self.assertAlmostEqual(result['support_reactions_N'][4],13.798275812071221,places=6)
        self.assertLess(result['complementarity_residual'],1e-7)
        self.assertIsNone(result['stability_pass'])

if __name__=='__main__':unittest.main()
