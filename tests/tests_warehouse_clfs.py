#emacs: -*- mode: python-mode; py-indent-offset: 4; indent-tabs-mode: nil -*-
#ex: set sts=4 ts=4 sw=4 et:
### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ##
#
#   See COPYING file distributed along with the PyMVPA package for the
#   copyright and license terms.
#
### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ##
"""Provides `clfs` dictionary with instances of all available classifiers."""

__docformat__ = 'restructuredtext'

#
# first deal with classifiers which do not have external deps
#
from mvpa.clfs.smlr import SMLR
from mvpa.clfs.ridge import RidgeReg
from mvpa.clfs.knn import *

clfs = {}
clfs['LinearC'] = [ SMLR(implementation="Python"),
                    SMLR(implementation="C"),
                    RidgeReg()]
clfs['NonLinearC'] = [ kNN(k=1) ]

#
# and now make all stuff with external deps completely optional
#
from mvpa.base import externals

# if have ANY svm implementation
if externals.exists('libsvm') or externals.exists('shogun'):
    from mvpa.clfs.svm import *
    clfs['LinearSVMC'] = []
    clfs['NonLinearSVMC'] = []

# libsvm check
if externals.exists('libsvm'):
    clfs['LinearSVMC'] += [libsvm.svm.LinearCSVMC(probability=1),
                           libsvm.svm.LinearNuSVMC(probability=1)]
    clfs['NonLinearSVMC'] += [libsvm.svm.RbfCSVMC(probability=1),
                              libsvm.svm.RbfNuSVMC(probability=1)]

# shogun svm check
if externals.exists('shogun'):
    clfs['LinearSVMC'].append(sg.svm.LinearCSVMC())
    clfs['NonLinearSVMC'].append(sg.svm.RbfCSVMC())

# finalize SVMs
if len(clfs.get('LinearSVMC', [])):
    # Make generic import
    from mvpa.clfs.svm import LinearCSVMC, RbfCSVMC
    clfs['SVMC'] = clfs['LinearSVMC'] + clfs['NonLinearSVMC']
    clfs['LinearC'] += clfs['LinearSVMC']
    clfs['NonLinearC'] += clfs['NonLinearSVMC']

# lars from R via RPy
if externals.exists('lars'):
    from mvpa.clfs.lars import LARS
    #clfs['LinearC'].append(LARS())


# finally merge them all
clfs['all'] = clfs['LinearC'] + clfs['NonLinearC']

# RidgeReg does not have a corresponding sensitivity analyzer yet
clfs['clfs_with_sens'] =  [ i for i in clfs['LinearC'] if not isinstance(i, RidgeReg) ]

