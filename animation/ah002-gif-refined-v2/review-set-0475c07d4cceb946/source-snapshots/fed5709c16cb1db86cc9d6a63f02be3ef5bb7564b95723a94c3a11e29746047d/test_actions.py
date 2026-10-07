"""Material invariants for offline authoring; synthetic fixtures never become assets."""
import sys,unittest
from pathlib import Path
import numpy as np
from PIL import Image
sys.path.insert(0,str(Path(__file__).resolve().parent))
from actions import Steam,SurfaceFlow,RigidPlant,StableFloat,RigidDrift,rotation,ChimneySmoke,Insect
from rigs import prepare

class MaterialTests(unittest.TestCase):
    def fixture(self):
        y,x=np.mgrid[:64,:64];alpha=np.where((x>8)&(x<56)&(y>5)&(y<61),np.minimum(255,(x-8)*12),0).astype('uint8')
        return Image.fromarray(np.dstack([np.full_like(alpha,210),np.full_like(alpha,160),np.full_like(alpha,95),alpha]))
    def test_exact_original_first_frame(self):
        image=self.fixture()
        actors=[ChimneySmoke(image),Steam(image),SurfaceFlow(image),SurfaceFlow(image,'flame'),RigidPlant(image,(32,60),.8,.5),StableFloat(image),RigidDrift(image,[2.2,-.6])]
        for actor in actors:self.assertEqual(actor.frame(0).tobytes(),image.tobytes(),type(actor).__name__)
    def test_fluid_alpha_and_uncontaminated_color(self):
        image=self.fixture();expected=np.asarray(image);visible=expected[:,:,3]>0
        for kind in ['water','flame']:
            actor=SurfaceFlow(image,kind)
            for frame in range(75):
                actual=np.asarray(actor.frame(frame*.04))
                self.assertTrue(np.array_equal(actual[:,:,3],expected[:,:,3]))
                # A uniform colored translucent source must never acquire black
                # fringes by sampling its transparent surroundings.
                self.assertLessEqual(int(np.abs(actual[:,:,:3].astype(int)-expected[:,:,:3]).max()),1)
                self.assertTrue(np.isfinite(actual).all())
    def test_rigid_geometry_and_no_forced_return(self):
        for angle in [-1.2,-.4,0,.8,1.7]:
            matrix=rotation(angle)
            self.assertTrue(np.allclose(matrix.T@matrix,np.eye(2),atol=1e-12))
            self.assertAlmostEqual(np.linalg.det(matrix),1.0)
        image=self.fixture()
        for actor in [ChimneySmoke(image),Steam(image),RigidPlant(image,(32,60),.8,.5),StableFloat(image),RigidDrift(image,[2.2,-.6])]:
            self.assertNotEqual(actor.frame(0).tobytes(),actor.frame(2.96).tobytes(),type(actor).__name__)
    def test_resting_material_is_exactly_unchanged(self):
        image=self.fixture();painted,actor,offset,_=prepare(image,{'action':'fixed_solid'},image.size)
        self.assertIsNone(actor);self.assertEqual(offset,(0,0));self.assertEqual(painted.tobytes(),image.tobytes())

    def test_independent_insect_clocks_preserve_opening_and_body(self):
        image=self.fixture()
        def actor(frequency,delay):
            item=Insect(image,[0,-1],[32,32],0,'butterfly',
                [[(29,0),(35,0),(35,63),(29,63)]],
                [[(0,0),(29,0),(29,63),(0,63)],[(35,0),(63,0),(63,63),(35,63)]])
            item.velocity_override=[0,0];item.wing_frequency=frequency;item.wing_delay=delay
            return item
        first=actor(2.83,0);delayed=actor(3.71,.23)
        self.assertEqual(first.frame(0).tobytes(),image.tobytes())
        self.assertEqual(delayed.frame(0).tobytes(),image.tobytes())
        self.assertNotEqual(first.frame(.64).tobytes(),delayed.frame(.64).tobytes())
        self.assertNotEqual(first.frame(0).tobytes(),first.frame(2.96).tobytes())
        self.assertNotEqual(delayed.frame(0).tobytes(),delayed.frame(2.96).tobytes())
        original=np.asarray(image)
        for time in [.04,.16,.32,.64,1.32,2.96]:
            self.assertTrue(np.array_equal(np.asarray(first.frame(time))[8:60,30:35],original[8:60,30:35]))
            self.assertTrue(np.array_equal(np.asarray(delayed.frame(time))[8:60,30:35],original[8:60,30:35]))

if __name__=='__main__':unittest.main()
