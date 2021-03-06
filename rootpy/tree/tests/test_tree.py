# Copyright 2012 the rootpy developers
# distributed under the terms of the GNU General Public License
from rootpy.math.physics.vector import LorentzVector
from rootpy.tree import Tree, TreeModel, TreeChain
from rootpy.io import open as ropen, TemporaryFile
from rootpy.types import FloatCol, IntCol
from rootpy.plotting import Hist, Hist2D, Hist3D
from rootpy import stl

from random import gauss, randint, random
import re

from nose.tools import assert_raises, assert_almost_equal, assert_equals
from unittest import TestCase


class TreeTests(TestCase):

    files = []
    file_paths = []

    @classmethod
    def setup_class(cls):

        class ObjectA(TreeModel):
            # A simple tree object
            x = FloatCol()
            y = FloatCol()
            z = FloatCol()

        class ObjectB(TreeModel):
            # A tree object collection
            x = stl.vector('int')
            y = stl.vector('float')
            vect = stl.vector('TLorentzVector')
            # collection size
            n = IntCol()

        class Event(ObjectA.prefix('a_') + ObjectB.prefix('b_')):
            i = IntCol()

        for i in range(5):
            f = TemporaryFile()
            tree = Tree("tree", model=Event)
            # fill the tree
            for i in xrange(10000):
                tree.a_x = gauss(.5, 1.)
                tree.a_y = gauss(.3, 2.)
                tree.a_z = gauss(13., 42.)
                tree.b_vect.clear()
                tree.b_x.clear()
                tree.b_y.clear()
                tree.b_n = randint(1, 5)
                for j in xrange(tree.b_n):
                    vect = LorentzVector(
                            gauss(.5, 1.),
                            gauss(.5, 1.),
                            gauss(.5, 1.),
                            gauss(.5, 1.))
                    tree.b_vect.push_back(vect)
                    tree.b_x.push_back(randint(1, 10))
                    tree.b_y.push_back(gauss(.3, 2.))
                tree.i = i
                tree.fill()
            tree.write()
            cls.files.append(f)
            cls.file_paths.append(f.GetName())

    @classmethod
    def teardown_class(cls):

        for f in cls.files:
            f.close()

    def test_attrs(self):

        with ropen(self.file_paths[0]) as f:
            tree = f.tree
            tree.read_branches_on_demand(True)
            tree.define_object('a', 'a_')
            tree.define_collection('b', 'b_', 'b_n')
            for event in tree:
                # test a setattr before a getattr with caching
                new_a_y = random()
                event.a_y = new_a_y
                assert_almost_equal(event.a_y, new_a_y)

                assert_equals(event.a_x, event.a.x)
                assert_equals(len(event.b) > 0, True)

    def test_cuts(self):

        with ropen(self.file_paths[0]) as f:
            tree = f.tree
            h1 = Hist(10, -1, 2)
            h2 = Hist2D(10, -1, 2, 10, -1, 2)
            h3 = Hist3D(10, -1, 2, 10, -1, 2, 10, -1, 2)

            tree.draw('a_x', hist=h1)
            assert_equals(h1.Integral() > 0, True)
            tree.draw('a_x:a_y', hist=h2)
            assert_equals(h2.Integral() > 0, True)
            tree.draw('a_x:a_y:a_z', hist=h3)
            assert_equals(h3.Integral() > 0, True)

            h3.Reset()
            tree.draw('a_x>0:a_y/2:a_z*2', hist=h3)
            assert_equals(h3.Integral() > 0, True)

    def test_chain_draw(self):

        chain = TreeChain('tree', self.file_paths)
        hist = Hist(100, 0, 1)
        chain.draw('a_x', hist=hist)
        assert_equals(hist.Integral() > 0, True)

        # check that Draw can be repeated
        hist2 = Hist(100, 0, 1)
        chain.draw('a_x', hist=hist2)
        assert_equals(hist.Integral(), hist2.Integral())

    def test_chain_draw_hist_init_first(self):

        hist = Hist(100, 0, 1)
        chain = TreeChain('tree', self.file_paths)
        chain.draw('a_x', hist=hist)
        assert_equals(hist.Integral() > 0, True)


def test_draw_regex():

    p = Tree.DRAW_PATTERN
    m = re.match
    assert_equals(m(p, 'a') is not None, True)
    assert_equals(m(p, 'somebranch') is not None, True)
    assert_equals(m(p, 'x:y') is not None, True)
    assert_equals(m(p, 'xbranch:y') is not None, True)
    assert_equals(m(p, 'x:y:z') is not None, True)

    expr = '(x%2)>0:sqrt(y)>4:z/3'
    assert_equals(m(p, expr) is not None, True)

    redirect = '>>+histname(10, 0, 1)'
    expr_redirect = expr + redirect
    match = m(p, expr_redirect)
    groupdict = match.groupdict()
    assert_equals(groupdict['branches'], expr)
    assert_equals(groupdict['redirect'], redirect)
    assert_equals(groupdict['name'], 'histname')


if __name__ == "__main__":
    import nose
    nose.runmodule()
