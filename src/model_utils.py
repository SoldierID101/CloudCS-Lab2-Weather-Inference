# -*- coding: utf-8 -*-
import pandas as pd
import joblib
from sklearn.pipeline import Pipeline


# Функция инференса.
# Принимает:
# - in_model: загруженный pipeline
# - in_data: словарь с входными погодными признаками
# Возвращает словарь с предсказанной температурой.
def make_inference(in_model: Pipeline, in_data: dict) -> dict[str, float]:
    # Преобразуем словарь в DataFrame из одной строки.
    # Именно в таком формате pipeline получает входные признаки.
    temperature = in_model.predict(pd.DataFrame(in_data, index=[0]))[0]


    # Округляем результат до 3 знаков после запятой,
    # чтобы ответ выглядел аккуратно.
    return {"temperature": round(float(temperature), 3)}


# Функция загрузки модели из файла.
# Загружается сохраненный Scikit-Learn Pipeline.
def load_model(path: str) -> Pipeline:
    model: Pipeline = joblib.load(path)
    return model
