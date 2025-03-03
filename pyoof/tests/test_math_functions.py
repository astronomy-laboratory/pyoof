#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Author: Tomas Cassanelli
import pytest
from scipy import interpolate
import numpy as np
from astropy import units as apu
from astropy.tests.helper import assert_quantity_allclose
from astropy.utils.misc import NumpyRNGContext
from astropy.utils.data import get_pkg_data_filename
from numpy.testing import assert_allclose, assert_equal
import pyoof


def test_norm():

    P_norm_a0_true = np.array([
        [1., 1., 1.],
        [0., 0., 0.],
        [0.6007134, 0.4391492, 0.38555163]
        ], dtype=np.float32
        )

    P_norm_a1_true = np.array([
        [1.25356787e-03, 2.08338746e-03, 2.59757042e-03,
        1.17263570e-03, 1.53579470e-03, 1.95269845e-03],
        [3.90828654e-06, 7.74897035e-06, 1.10233095e-05,
        2.67764717e-05, 2.45369101e-05, 1.83909979e-05],
        [7.22095836e-04, 9.35678603e-04, 1.07243832e-03,
        1.62301958e-03, 1.22317078e-03, 6.73963455e-04]
        ], dtype=np.float32
        )
    data_info, data_obs = pyoof.extract_data_pyoof(
        get_pkg_data_filename('data/data_simulated.fits')
        )
    [beam_data, _, _] = data_obs

    P_norm_a0 = pyoof.norm(beam_data, axis=0)
    P_norm_a1 = pyoof.norm(beam_data, axis=1)
    P_norm_aNone = pyoof.norm(beam_data[0, ...], axis=None)

    # axis = 0
    assert_allclose(P_norm_a0[:, :3], P_norm_a0_true)

    # axis = 1
    assert_allclose(P_norm_a1[:, :3], P_norm_a1_true[:, :3])
    assert_allclose(P_norm_a1[:, -3:], P_norm_a1_true[:, -3:])

    # axis = None
    assert_allclose(P_norm_aNone[:3], P_norm_a1_true[0, :3])


def test_cart2pol():

    with NumpyRNGContext(0):
        x = np.random.uniform(-1, 1, 5)
        y = np.random.uniform(-1, 1, 5)

    rho, theta = pyoof.cart2pol(x, y)

    rho_true = np.array([
        0.30768718, 0.44811525, 0.81005283, 0.93166014, 0.27867163
        ])
    theta_true = np.array([
        1.24792264, -0.28229117, 1.31427197, 1.47429564, -2.15067483
        ])

    assert_allclose(rho, rho_true)
    assert_allclose(theta, theta_true)


def test_co_matrices():

    # importing tests files
    res = np.load(
        get_pkg_data_filename('data/res_co_matrices.npy')
        )
    jac = np.load(
        get_pkg_data_filename('data/jac_co_matrices.npy')
        )
    cov_true = np.load(
        get_pkg_data_filename('data/cov_co_matrices.npy')
        )
    corr_true = np.load(
        get_pkg_data_filename('data/corr_co_matrices.npy')
        )

    cov, corr = pyoof.co_matrices(res, jac, 1)

    assert_allclose(cov, cov_true)
    assert_allclose(corr, corr_true)


def test_line_equation():

    x = np.linspace(-1, 1, 10)
    y1 = pyoof.line_equation((0, 0), (1, 1,), x)
    y1_true = x

    with NumpyRNGContext(0):
        p1 = (np.random.uniform(0, 1), np.random.uniform(0, 1))
        p2 = (np.random.uniform(0, 1), np.random.uniform(0, 1))

    y2 = pyoof.line_equation(p1, p2, x)
    y2_true = np.array([
        5.604404226951, 4.902904538006, 4.20140484906, 3.499905160114,
        2.798405471169, 2.096905782223, 1.395406093278, 0.693906404332,
        -0.007593284613, -0.709092973559
        ])

    assert_allclose(y1, y1_true)
    assert_allclose(y2, y2_true)


def test_rms():

    x1 = np.array([1] * 10 + [-1] * 10)
    rms1 = pyoof.rms(x1, False)
    rms1_true = 1.0

    with NumpyRNGContext(0):
        x2 = np.random.uniform(-20, 20, 5)
    rms2 = pyoof.rms(x2, False)
    rms2_true = 4.6335342124813295

    with NumpyRNGContext(1):
        x3 = np.random.uniform(-20, 20, 100).reshape(10, -1)
    rms3 = pyoof.rms(x3, True)
    rms3_true = 11.665405508342806

    assert_equal(rms1, rms1_true)
    assert_equal(rms2, rms2_true)
    assert_quantity_allclose(rms3, rms3_true)

def test_snr():

    # ndim = 1
    snr_list_1dim_true = np.array([149.859673, 15563.025383, 235.739288])
    data_info, data_obs = pyoof.extract_data_pyoof(
        get_pkg_data_filename('data/data_simulated.fits')
        )
    [beam_data, u_data, v_data] = data_obs

    snr_list_1dim = np.zeros((3, ), dtype=np.float64)
    for i in range(3):
        snr_list_1dim[i] = pyoof.snr(
            beam_data=beam_data[i],
            u_data=u_data[i],
            v_data=v_data[i],
            centre=.04 * apu.deg,
            radius=.01 * apu.deg
            )

    assert_allclose(snr_list_1dim, snr_list_1dim_true)

    # ndim != 1
    snr_list_ndim = np.zeros((3, ), dtype=np.float64)
    for k in range(beam_data.shape[0]):
        u_ng = np.linspace(u_data[k, :].min(), u_data[k, :].max(), 300)
        v_ng = np.linspace(v_data[k, :].min(), v_data[k, :].max(), 300)

        beam_ng = interpolate.griddata(
            points=(u_data[k, :], v_data[k, :]),
            values=beam_data[k, :],
            xi=tuple(np.meshgrid(u_ng, v_ng)),
            method='cubic'
            )

        snr_list_ndim[k] = pyoof.snr(
            beam_data=beam_ng,
            u_data=u_ng,
            v_data=v_ng,
            centre=.04 * apu.deg,
            radius=.01 * apu.deg
            )

    assert_allclose(snr_list_ndim, snr_list_1dim_true)
