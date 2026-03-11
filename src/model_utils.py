# -*- coding: utf-8 -*-
import pandas as pd
import joblib
from sklearn.pipeline import Pipeline


def make_inference(in_model: Pipeline, in_data: dict) -> dict[str, float]:
    temperature = in_model.predict(pd.DataFrame(in_data, index=[0]))[0]
    return {"temperature": round(float(temperature), 3)}


def load_model(path: str) -> Pipeline:
    model: Pipeline = joblib.load(path)
    return model
