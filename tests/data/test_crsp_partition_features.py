import pandas as pd

from ath_breakout.data.crsp_processing import (
    add_stateful_crsp_features,
    initialize_crsp_feature_state,
    normalize_crsp_strategy_rows,
    restore_crsp_feature_state,
)
from tests.data.test_crsp_processing import crsp_rows


def test_features_continue_exactly_across_partition_boundary() -> None:
    raw = crsp_rows(205)
    first, _ = normalize_crsp_strategy_rows(raw.iloc[:199])
    second, _ = normalize_crsp_strategy_rows(raw.iloc[199:])
    state = initialize_crsp_feature_state()

    first_result = add_stateful_crsp_features(first, state)
    second_result = add_stateful_crsp_features(second, state)

    assert pd.isna(first_result.iloc[-1]["sma_200"])
    assert second_result.iloc[0]["sma_200"] == 99.75
    assert second_result.iloc[0]["prior_ath"] == 149.5
    assert bool(second_result.iloc[0]["breakout"]) is False


def test_seed_is_carried_into_first_partition() -> None:
    raw = crsp_rows(2)
    canonical, _ = normalize_crsp_strategy_rows(raw)
    seed = pd.DataFrame({"permno": [14593], "prior_comparable_high": [200.0]})
    state = initialize_crsp_feature_state(seed)

    result = add_stateful_crsp_features(canonical, state)

    assert result["prior_ath"].tolist() == [200.0, 200.0]


def test_resume_combines_short_tails_from_multiple_partitions() -> None:
    canonical, _ = normalize_crsp_strategy_rows(crsp_rows(201))
    state = initialize_crsp_feature_state()
    restore_crsp_feature_state(canonical.iloc[:100], state)
    restore_crsp_feature_state(canonical.iloc[100:199], state)

    result = add_stateful_crsp_features(canonical.iloc[199:], state)

    assert result.iloc[0]["sma_200"] == 99.75
