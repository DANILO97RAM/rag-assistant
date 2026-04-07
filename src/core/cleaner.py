import pandas as pd
import json
import re
from typing import Optional

class TextCleaner:

    _PATTERNS = {
        "html": re.compile(r"<[^>]+>"),
        "html_entities": re.compile(r"&[a-zA-Z0-9#]+;"),
        "headers": re.compile(r"#{1,6}\s*"),
        "links": re.compile(r"\[([^\]]+)\]\([^\)]+\)"),
        "images": re.compile(r"!\[([^\]]+)\]\([^\)]+\)"),
        "bold_italic": re.compile(r"\*\*|\*|__|_"),
        "lists": re.compile(r"^\s*[\*\-+]\s*", re.MULTILINE),
        "code": re.compile(r"`{1,3}"),
        "template_vars": re.compile(r"\$\{[^\}]+\}"),
    }

    _METADATA_TO_CLEAN = {"subtopic", "topic", "possible_query"}
    _EXPECTED_COLS = {"id", "metadata", "texto"}

    def __init__(self, df: pd.DataFrame, logger=None):
        self.df = df.copy()
        self.tag = "==>[TextCleaner]"
        self.logger = logger

    @staticmethod
    def _clean_text(text: str) -> Optional[str]:
        if not isinstance(text, str):
            return text
        for pattern in TextCleaner._PATTERNS.values():
            text = pattern.sub("", text)
        cleaned = text.strip()
        return cleaned if cleaned else None

    @staticmethod
    def _clean_metadata(metadata: str) -> str:
        try:
            data = json.loads(metadata) if isinstance(metadata, str) else metadata
            for key in TextCleaner._METADATA_TO_CLEAN:
                if key in data and isinstance(data[key], str):
                    data[key] = TextCleaner._clean_text(data[key])
            return json.dumps(data)
        except Exception:
            return metadata

    def _validate_dataframe(self, process_path: str = ""):
        if "metadata" in self.df.columns and self.df["metadata"].dtype == object:
            if self.df["metadata"].apply(lambda x: isinstance(x, dict)).any():
                if self.logger:
                    self.logger.warning(f"{self.tag} 'metadata' column contains dicts, converting to JSON string")
                self.df["metadata"] = self.df["metadata"].apply(
                    lambda x: json.dumps(x) if isinstance(x, dict) else x
                )

        missing_columns = self._EXPECTED_COLS - set(self.df.columns)
        if missing_columns:
            missing_str = ", ".join(sorted(missing_columns))
            raise ValueError(f"{self.tag} Columns: --{missing_str}-- not found in the DataFrame. File(s): {process_path}")

        null_counts = {col: int(self.df[col].isna().sum()) for col in self._EXPECTED_COLS}
        columns_with_nulls = {col: count for col, count in null_counts.items() if count > 0}

        if columns_with_nulls:
            null_cols_str = ", ".join(f"{col}: {count}" for col, count in sorted(columns_with_nulls.items()))
            raise ValueError(f"{self.tag} The following columns contain null values: {null_cols_str} in file(s) {process_path}")

    def transform(self, process_path: str = "") -> pd.DataFrame:
        self._validate_dataframe(process_path)

        if self.logger:
            self.logger.debug(f"{self.tag} Checked DataFrame structure and null values")

        df = self.df.copy()

        # --- Limpieza de 'texto' ---
        def apply_patterns(text: str) -> str:
            if not isinstance(text, str):
                return text
            for pattern in self._PATTERNS.values():
                text = pattern.sub("", text)
            return text.strip()

        df["texto"] = df["texto"].apply(apply_patterns)

        empty_mask = df["texto"] == ""
        empty_count = empty_mask.sum()
        if empty_count > 0:
            if self.logger:
                self.logger.warning(
                    f"{self.tag} Column 'texto' has {empty_count} empty strings after cleaning in process file(s) {process_path}"
                )
            df.loc[empty_mask, "texto"] = "<empty from source>"

        # --- Limpieza de 'metadata' ---
        df["metadata"] = df["metadata"].apply(self._clean_metadata)

        return df