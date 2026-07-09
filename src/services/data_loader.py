import pandas as pd

from src.config import (
    RECREACION_CSV,
    OPINIONES_CSV,
    BALNEARIOS_CSV,
    CSV_SEPARATOR,
    CSV_ENCODINGS,
)


def _load_csv(path, encoding):
    return pd.read_csv(path, sep=CSV_SEPARATOR, encoding=encoding, dtype=str)


def _normalize_column(series: pd.Series) -> pd.Series:
    return series.str.lower().str.strip()


def load_all_dataframes():
    recreacion = _load_csv(RECREACION_CSV, CSV_ENCODINGS["recreacion"])
    opiniones = _load_csv(OPINIONES_CSV, CSV_ENCODINGS["opiniones"])
    balnearios = _load_csv(BALNEARIOS_CSV, CSV_ENCODINGS["balnearios"])
    return recreacion, opiniones, balnearios


def load_merged_data():
    recreacion, opiniones, _ = load_all_dataframes()
    recreacion["_join_key"] = _normalize_column(recreacion["descripcion"])
    opiniones["_join_key"] = _normalize_column(opiniones["descripcion"])
    merged = recreacion.merge(opiniones, on="_join_key", how="left", suffixes=("", "_opinion"))
    merged.drop(columns=["_join_key"], inplace=True)
    return merged, recreacion, opiniones
