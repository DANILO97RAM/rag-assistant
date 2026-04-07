"""
Función principal del programa. 
Primero se llama al scrping y lo convierte en df, limpia el df, genera el chunk, y luego carga la base de conocimiento a la db.

"""
import pandas as pd
from core.scrapper import run_scrapping
from core.cleaner import TextCleaner
from core.chunker import Chunker
#from src.services.database import load_knowledge_base

def run():

    
    df = pd.DataFrame()  # Inicializar df vacío
    df = run_scrapping()
    cleaner = TextCleaner(df)  # Inicializar con DataFrame vacío
    df = cleaner.transform()  # Transformar el DataFrame vacío, lo que validará su estructura
    chunker = Chunker()
    df = chunker.get_chunks(df)
    # load_knowledge_base(df)

if __name__ == "__main__":
    run()  