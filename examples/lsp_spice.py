#!/usr/bin/env python

'''This script uses SPICE to compute a trajectory for the sun, loads a
shape model discretizing a patch of the lunar south pole (made using
lsp_make_obj.py), and a compressed form factor matrix for that
shape model (computed using lsp_compress_form_factor_matrix.py).
It then proceeds to compute the steady state temperature at each sun
position, writing a plot of the temperature to disk for each sun
position.

'''

import colorcet as cc
import matplotlib.pyplot as plt
import numpy as np
import pickle
import spiceypy as spice

from pathlib import Path

import flux.compressed_form_factors as cff

from flux.form_factors import get_form_factor_block
from flux.model import compute_steady_state_temp
from flux.plot import tripcolor_vector
from flux.shape import TrimeshShapeModel
from flux.util import tic, toc

clktol = '10:000'

spice.kclear()
spice.furnsh('simple.furnsh')

# Define time window

et0 = spice.str2et('2011 MAR 01 00:00:00.00')
et1 = spice.str2et('2011 APR 01 00:00:00.00')
et = np.linspace(et0, et1, 100, endpoint=False)

# Sun positions over time period

possun = spice.spkpos('SUN', et, 'MOON_ME', 'LT+S', 'MOON')[0]
lonsun = np.arctan2(possun[:, 1], possun[:, 0])
lonsun = np.mod(lonsun, 2*np.pi)
radsun = np.sqrt(np.sum(possun[:, :2]**2, axis=1))
latsun = np.arctan2(possun[:, 2], radsun)

sun_dirs = np.array([
    np.cos(lonsun)*np.cos(latsun),
    np.sin(lonsun)*np.cos(latsun),
    np.sin(latsun)
]).T

# Use these temporary parameters...

F0 = 1365 # Solar constant
emiss = 0.95 # Emissitivity
rho = 0.12 # Visual (?) albedo

# Load shape model

V = np.load('lsp_V.npy')
F = np.load('lsp_F.npy')
N = np.load('lsp_N.npy')

shape_model = TrimeshShapeModel(V, F, N)

# Load compressed form factor matrix from disk

FF_path = 'lsp_compressed_form_factors.bin'
FF = cff.CompressedFormFactorMatrix.from_file(FF_path)

FF_gt = get_form_factor_block(shape_model)

# Compute steady state temperature
E_arr = []
for i, sun_dir in enumerate(sun_dirs[:]):
    E_arr.append(shape_model.get_direct_irradiance(F0, sun_dir))

E = np.vstack(E_arr).T
T_arr = compute_steady_state_temp(FF, E, rho, emiss)
T = np.vstack(T_arr).T

Path('./frames').mkdir(parents=True, exist_ok=True)

for i, sun_dir in enumerate(sun_dirs[:]):
    print('frame = %d' % i)

    fig, ax = tripcolor_vector(V, F, E[:,i], cmap=cc.cm.gray)
    fig.savefig('./frames/lsp_E1_%03d.png' % i)
    plt.close(fig)

    fig, ax = tripcolor_vector(V, F, T[:,i], cmap=cc.cm.fire)
    fig.savefig('./frames/lsp_T1_%03d.png' % i)
    plt.close(fig)

    I_shadow = E[:,i] == 0
    fig, ax = tripcolor_vector(V, F, T[:,i], I=I_shadow, cmap=cc.cm.rainbow, vmax=100)
    fig.savefig('./frames/lsp_T1_shadow_%03d.png' % i)
    plt.close(fig)
