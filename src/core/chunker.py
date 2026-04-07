from langchain_text_splitters import RecursiveCharacterTextSplitter
import pandas as pd


class Chunker:
    def __init__(
        self,
        model_name: str = "gpt-4o",
        chunk_size: int = 1024,
        chunk_overlap: int = 0,
        logger=None,
    ):
        self.tag = "[Chunker]"
        self.logger = logger
        self.splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
            model_name=model_name,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )

    def get_chunks(self, df: pd.DataFrame) -> pd.DataFrame:
        if self.logger:
            self.logger.debug(f"{self.tag} Starting chunking process for {len(df)} rows")

        df = df.copy()
        df["texto"] = df["texto"].apply(
            lambda t: self.splitter.split_text(t) if isinstance(t, str) else []
        )

        df_chunks = (
            df.explode("texto")
              .reset_index(drop=True)
        )

        if self.logger:
            self.logger.debug(f"{self.tag} Generated {len(df_chunks)} chunks from {len(df)} rows")

        return df_chunks