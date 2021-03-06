#!/usr/bin/env python
"""
============================================
Copy a tree chain while overwriting branches
============================================

This is an example showing how to copy a tree chain while overwriting one or
more of its branches with new values.
"""
print __doc__
import rootpy
rootpy.log.basic_config_colorized()
from rootpy.tree import Tree, TreeModel, TreeChain
from rootpy.io import open as ropen
from rootpy.types import FloatCol, IntCol
from random import gauss

"""
This first section of code only creates an example tree chain.
"""

class Event(TreeModel):
    """Event model definition"""
    x = FloatCol()
    y = FloatCol()
    z = FloatCol()
    i = IntCol()

# first create several example trees in separate files
fnames = ["test_%d.root" % i for i in xrange(10)]

for fname in fnames:
    with ropen(fname, "recreate") as f:

        tree = Tree("test", model=Event)

        # fill the tree
        for i in xrange(10000):
            tree.x = gauss(.5, 1.)
            tree.y = gauss(.3, 2.)
            tree.z = gauss(13., 42.)
            tree.i = i
            tree.fill()
        tree.write()

"""
This section below takes the example trees and copies it while overwriting a
branch with new values.
"""

# first define the chain of trees
chain = TreeChain(name="test", files=fnames)

# Now we want to copy the tree above into a new file while overwriting a branch
# First create a new file to save the new tree in:
f_copy = ropen("test_copy.root", "recreate")

# You may not know the entire model of the original tree but only the branches
# you intend to overwrite, so I am not specifying the model=Event below as an
# example of how to deal with this in general:
tree_copy = Tree("test_copy")

# If the original tree was not handed to you through rootpy don't forget to:
# >>> from rootpy.utils import asrootpy
# >>> tree = asrootpy(tree)

# Here we specify the buffer for the new tree to use. We use the same buffer as
# the original tree. This creates all the same branches in the new tree but
# their addresses point to the same memory used by the original tree.
tree_copy.set_buffer(
        chain._buffer,
        create_branches=True)

# Now loop over the original tree and fill the new tree
for entry in chain:
    # Overwrite a branch value. This changes the value that will be written to
    # the new tree but leaves the value unchanged in the original tree on disk.
    entry.x = 3.141
    # "entry" is actually the buffer, which is shared between both trees.
    tree_copy.Fill()

# tree_copy is now a copy of tree where the "x" branch has been overwritten
# with new values
tree_copy.Write()
f_copy.Close()
