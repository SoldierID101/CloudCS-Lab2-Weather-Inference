# -*- coding: utf-8 -*-

from pickle import dumps

import pandas as pd
import pytest
from sklearn.pipeline import Pipeline

from model_utils import load_model, make_inference


@pytest.fixture
def create_data() -> dict[str, int | float]:
    return {
        "hour": 12,
        "month": 6,
        "precipitation": 0.0,
        "pressure": 1008.0,
        "humidity": 75.0,
        "wind_speed": 3.5,
        "latitude": -3.1,
        "longitude": -60.0,
        "height": 61.25,
    }


def test_make_inference(monkeypatch, create_data) -> None:
    def mock_get_predictions(_, data: pd.DataFrame):
        assert create_data == {
            key: value[0] for key, value in data.to_dict("list").items()
        }
        return [27.8]

    in_model = Pipeline([])

    monkeypatch.setattr(Pipeline, "predict", mock_get_predictions)

    result = make_inference(in_model, create_data)
    assert result == {"temperature": 27.8}


@pytest.fixture
def filepath_and_data(tmpdir):
    path_obj = tmpdir.mkdir("datadir").join("fakedmodel.pkl")
    example = "Test message!"
    path_obj.write_binary(dumps(example))
    return str(path_obj), example


def test_load_model(filepath_and_data) -> None:
    filepath, expected_data = filepath_and_data
    assert expected_data == load_model(filepath)
