import itertools

import pandas as pd
import pytest
from pandas.testing import assert_series_equal

from gettsim import compute_taxes_and_transfers
from gettsim import set_up_policy_environment
from gettsim.config import ROOT_DIR


INPUT_COLS = [
    "p_id",
    "tu_id",
    "hh_id",
    "grundr_zeiten",
    "grundr_bew_zeiten",
    "wohnort_ost",
    "proxy_rente_vorj_vor_grundr_m",
    "bruttolohn_vorj_m",
    "brutto_eink_1",
    "brutto_eink_6",
    "kapitaleink_minus_pauschbetr",
    "alter",
    "alleinstehend",
    "geburtsjahr",
    "bruttolohn_m",
    "entgeltp",
    "ges_rente_zugangsfaktor",
    "rentner",
    "grundr_entgeltp",
    "kind",
]


YEARS = [2021]

OUT_COLS_TOL = {
    "grundr_zuschlag_bonus_entgeltp": 0.0001,
    "grundr_zuschlag_vor_eink_anr_m": 1,
    "grundr_zuschlag_m": 1,
    "ges_rente_m": 1,
}
OUT_COLS = OUT_COLS_TOL.keys()


@pytest.fixture(scope="module")
def input_data():
    file_name = "test_dfs_grundrente.csv"
    out = pd.read_csv(ROOT_DIR / "tests" / "test_data" / file_name)
    out["p_id"] = out["p_id"].astype(int)
    return out


@pytest.mark.parametrize("year, column", itertools.product(YEARS, OUT_COLS))
def test_grundrente(input_data, year, column):
    year_data = input_data[input_data["jahr"] == year]
    df = year_data[INPUT_COLS].copy()
    policy_params, policy_functions = set_up_policy_environment(date=f"{year}-07-01")

    calc_result = compute_taxes_and_transfers(
        data=df,
        params=policy_params,
        functions=policy_functions,
        targets=column,
        columns_overriding_functions=[
            "proxy_rente_vorj_vor_grundr_m",
            "brutto_eink_1",
            "brutto_eink_6",
            "kapitaleink_minus_pauschbetr",
            "ges_rente_zugangsfaktor",
        ],
    )
    tol = OUT_COLS_TOL[column]
    assert_series_equal(calc_result[column], year_data[column], atol=tol)


INPUT_COLS_INCOME = [
    "p_id",
    "tu_id",
    "hh_id",
    "alter",
    "priv_rente_m",
    "entgeltp",
    "geburtsjahr",
    "rentner",
    "jahr_renteneintr",
    "wohnort_ost",
    "bruttolohn_m",
]


@pytest.fixture(scope="module")
def input_data_proxy_rente():
    file_name = "test_dfs_grundrente_proxy_rente.csv"
    out = pd.read_csv(ROOT_DIR / "tests" / "test_data" / file_name)
    out["p_id"] = out["p_id"].astype(int)
    out["jahr_renteneintr"] = out["jahr_renteneintr"].astype("Int64")

    return out


@pytest.mark.parametrize("year", YEARS)
def test_proxy_rente_vorj(input_data_proxy_rente, year):
    year_data = input_data_proxy_rente[input_data_proxy_rente["jahr"] == year]
    df = year_data[INPUT_COLS_INCOME].copy()
    policy_params, policy_functions = set_up_policy_environment(date=f"{year}-07-01")
    target = "proxy_rente_vorj_vor_grundr_m"
    calc_result = compute_taxes_and_transfers(
        data=df, params=policy_params, functions=policy_functions, targets=target,
    )
    assert_series_equal(calc_result[target].astype(float), year_data[target])


@pytest.mark.parametrize("year", YEARS)
def test_proxy_rente_vorj_comparison_last_year(input_data_proxy_rente, year):
    year_data = input_data_proxy_rente[input_data_proxy_rente["jahr"] == year]
    df = year_data[INPUT_COLS_INCOME].copy()
    policy_params, policy_functions = set_up_policy_environment(date=f"{year}-07-01")

    calc_result = compute_taxes_and_transfers(
        data=df,
        params=policy_params,
        functions=policy_functions,
        targets="proxy_rente_vorj_vor_grundr_m",
    )

    # Calculate pension of last year
    policy_params, policy_functions = set_up_policy_environment(
        date=f"{year - 1}-07-01"
    )
    df["alter"] -= 1
    calc_result_last_year = compute_taxes_and_transfers(
        data=df,
        params=policy_params,
        functions=[policy_functions],
        targets=["ges_rente_vor_grundr_m"],
        # rounding=False,
    )
    assert_series_equal(
        calc_result["proxy_rente_vorj_vor_grundr_m"],
        calc_result_last_year["ges_rente_vor_grundr_m"] + year_data["priv_rente_m"],
        check_names=False,
    )
