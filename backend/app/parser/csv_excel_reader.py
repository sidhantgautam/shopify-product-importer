import pandas as pd
from typing import List, Dict
from pathlib import Path

def read_file(file_path: str) -> List[Dict]:
    
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    if path.suffix.lower() == ".csv":
        df = pd.read_csv(path)
    elif path.suffix.lower() in [".xls", ".xlsx"]:
        df = pd.read_excel(path)
    else:
        raise ValueError("Unsupported file type. Only CSV and Excel are supported.")

    df = df.where(pd.notnull(df), None)

    return df.to_dict(orient="records")
