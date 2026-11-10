"""Tests for analyses/evaluation.py and Aim 3 helpers."""

import os
import sys

import numpy as np
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import common as cm  # noqa: E402
from evaluation import calibration, net_benefit, net_benefit_treat_all  # noqa: E402


def test_calibration_of_well_calibrated_predictions():
    rng = np.random.default_rng(0)
    p = rng.uniform(0.05, 0.95, 20000)
    y = rng.random(20000) < p
    c = calibration(y, p)
    assert c["cal_slope"] == pytest.approx(1.0, abs=0.05)
    assert c["cal_intercept"] == pytest.approx(0.0, abs=0.05)


def test_calibration_detects_overconfidence():
    rng = np.random.default_rng(1)
    lp = rng.normal(0, 1, 20000)
    y = rng.random(20000) < 1 / (1 + np.exp(-lp))
    over = 1 / (1 + np.exp(-2 * lp))  # logits doubled -> slope ~0.5
    assert calibration(y, over)["cal_slope"] == pytest.approx(0.5, abs=0.05)


def test_net_benefit_hand_example():
    y = np.array([1, 1, 0, 0])
    p = np.array([0.9, 0.4, 0.6, 0.1])
    # t = 0.5: treated = {0.9 (TP), 0.6 (FP)} -> 1/4 - 1/4 * 1 = 0
    assert net_benefit(y, p, [0.5])[0] == pytest.approx(0.0)
    # t = 0.2: treated = {0.9, 0.4, 0.6} -> 2/4 - 1/4 * 0.25 = 0.4375
    assert net_benefit(y, p, [0.2])[0] == pytest.approx(0.4375)
    assert net_benefit_treat_all(y, [0.2])[0] == pytest.approx(0.5 - 0.5 * 0.25)


def test_compartment_groups_have_atlas_names():
    g = cm.brain_groups()
    for f in g["thickness"] + g["area"]:
        assert f.startswith(("lh_", "rh_"))
