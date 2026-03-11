# -*- coding: utf-8 -*-
import pytest
import pandas as pd
from model_utils import make_inference, load_model
from sklearn.pipeline import Pipeline
from pickle import dumps


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
        "height": 61.25
    }


def test_make_inference(monkeypatch, create_data):
    def mock_get_predictions(_, data: pd.DataFrame):
        assert create_data == {
            key: value[0] for key, value in data.to_dict("list").items()
        }
        return [27.8]

    in_model = Pipeline([])
    monkeypatch.setattr(Pipeline, "predict", mock_get_predictions)

    result = make_inference(in_model, create_data)
    assert result == {"temperature": 27.8}


@pytest.fixture()
def filepath_and_data(tmpdir):
    p = tmpdir.mkdir("datadir").join("fakedmodel.pkl")
    example: str = "Test message!"
    p.write_binary(dumps(example))
    return str(p), example


def test_load_model(filepath_and_data):
    assert filepath_and_data[1] == load_model(filepath_and_data[0])
