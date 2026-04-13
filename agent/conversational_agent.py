#!/usr/bin/env python3
"""
Agente Conversacional - Bancolombia Knowledge Assistant

Cliente MCP que consume el servidor MCP via API REST.
Razona sobre qué tool usar según la intención del usuario.
Mantiene memoria conversacional.

Requisito 3.5: Agente conversacional (Cliente MCP)

Uso:
    # Como librería
    from agent.conversational_agent import BancolombiaAgent
    agent = BancolombiaAgent()
    response = agent.ask("¿Qué seguros ofrece Bancolombia?")
    
    # Standalone CLI
    python agent/conversational_agent.py
"""

import requests
import re
from typing import Dict, List, Optional, Any
from datetime import datetime


class BancolombiaAgent:
    """
    Agente conversacional que actúa como cliente MCP.
    
    Consume las 3 tools del servidor MCP via API REST:
    - search_knowledge_base (POST /search)
    - get_article_by_url (GET /article)
    - list_categories (GET /categories)
    
    Mantiene memoria conversacional en tres niveles:
    - Corto plazo: Últimos 5 turnos de conversación
    - Mediano plazo: Resumen de temas discutidos en la sesión
    - Largo plazo: Base de conocimiento en ChromaDB (via MCP)
    """
    
    def __init__(self, api_url: str = "http://localhost:8001"):
        """
        Inicializa el agente conversacional.
        
        Args:
            api_url: URL base del API REST del servidor MCP
        """
        self.api_url = api_url
        self.historial_corto = []  # Memoria corto plazo (últimos 5 turnos)
        self.temas_discutidos = set()  # Memoria mediano plazo
        self.session_start = datetime.now()
        
    def ask(self, pregunta: str, n_results: int = 3) -> Dict[str, Any]:
        """
        Procesa una pregunta del usuario y retorna la respuesta del agente.
        
        Flujo:
        1. Razona sobre la intención del usuario
        2. Decide qué tool MCP invocar
        3. Ejecuta la consulta al servidor MCP
        4. Formatea la respuesta con fuentes
        5. Actualiza memoria conversacional
        
        Args:
            pregunta: Pregunta del usuario en lenguaje natural
            n_results: Número de resultados para búsquedas (default: 3)
            
        Returns:
            Dict con la respuesta formateada y metadata
        """
        # 1. Razonar sobre la intención
        intencion = self._analizar_intencion(pregunta)
        
        # 2. Decidir qué tool usar
        tool = self._decidir_tool(intencion, pregunta)
        
        # 3. Invocar el tool correspondiente del MCP
        try:
            respuesta = self._invocar_tool_mcp(tool, pregunta, n_results)
        except Exception as e:
            respuesta = {
                "error": True,
                "message": f"Error al consultar el servidor MCP: {str(e)}",
                "suggestion": "Verifica que el API REST esté ejecutándose (make mcp-up)"
            }
        
        # 4. Actualizar memoria conversacional
        self._actualizar_memoria(pregunta, respuesta, intencion)
        
        return respuesta
    
    def _analizar_intencion(self, pregunta: str) -> str:
        """
        Analiza la intención del usuario mediante heurísticas simples.
        
        Args:
            pregunta: Pregunta del usuario
            
        Returns:
            Intención detectada: 'busqueda', 'url', 'categorias', 'estadisticas', 'contexto'
        """
        pregunta_lower = pregunta.lower()
        
        # Detectar URL explícita
        if "https://" in pregunta or "http://" in pregunta:
            return "url"
        
        # Detectar solicitud de categorías
        if any(palabra in pregunta_lower for palabra in ["categoría", "categoria", "temas", "tópicos", "topicos"]):
            return "categorias"
        
        # Detectar solicitud de estadísticas
        if any(palabra in pregunta_lower for palabra in ["estadística", "estadistica", "cuántos", "cuantos", "total"]):
            return "estadisticas"
        
        # Detectar referencia a contexto previo
        if any(palabra in pregunta_lower for palabra in ["anterior", "lo que dijiste", "ese", "esa", "esto"]):
            return "contexto"
        
        # Por defecto: búsqueda semántica
        return "busqueda"
    
    def _decidir_tool(self, intencion: str, pregunta: str) -> str:
        """
        Decide qué tool del MCP invocar según la intención.
        
        Args:
            intencion: Intención detectada
            pregunta: Pregunta original
            
        Returns:
            Nombre del tool: 'search', 'article', 'categories', 'stats'
        """
        if intencion == "url":
            return "article"
        elif intencion == "categorias":
            return "categories"
        elif intencion == "estadisticas":
            return "stats"
        elif intencion == "contexto":
            # Si hace referencia al contexto previo, buscar en historial
            return "search"
        else:
            return "search"
    
    def _invocar_tool_mcp(self, tool: str, pregunta: str, n_results: int) -> Dict[str, Any]:
        """
        Invoca el tool correspondiente del servidor MCP via API REST.
        
        Args:
            tool: Nombre del tool ('search', 'article', 'categories', 'stats')
            pregunta: Pregunta del usuario
            n_results: Número de resultados
            
        Returns:
            Respuesta del servidor MCP formateada
        """
        if tool == "search":
            return self._search_knowledge_base(pregunta, n_results)
        elif tool == "article":
            url = self._extraer_url(pregunta)
            return self._get_article_by_url(url)
        elif tool == "categories":
            return self._list_categories()
        elif tool == "stats":
            return self._get_stats()
        else:
            return {"error": True, "message": f"Tool desconocido: {tool}"}
    
    def _search_knowledge_base(self, query: str, n_results: int) -> Dict[str, Any]:
        """
        Tool MCP: search_knowledge_base
        Endpoint: POST /search
        """
        try:
            response = requests.post(
                f"{self.api_url}/search",
                json={"query": query, "n_results": n_results},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "tool": "search_knowledge_base",
                    "success": True,
                    "query": query,
                    "total_results": data["total_results"],
                    "documents": data["documents"]
                }
            else:
                return {
                    "tool": "search_knowledge_base",
                    "success": False,
                    "error": f"Error HTTP {response.status_code}"
                }
        except Exception as e:
            raise Exception(f"Error en search_knowledge_base: {str(e)}")
    
    def _get_article_by_url(self, url: str) -> Dict[str, Any]:
        """
        Tool MCP: get_article_by_url
        Endpoint: GET /article
        """
        try:
            response = requests.get(
                f"{self.api_url}/article",
                params={"url": url},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "tool": "get_article_by_url",
                    "success": True,
                    "url": data["url"],
                    "title": data["title"],
                    "category": data["category"],
                    "chunks": data["chunks"]
                }
            elif response.status_code == 404:
                return {
                    "tool": "get_article_by_url",
                    "success": False,
                    "error": f"No se encontró artículo para la URL: {url}"
                }
            else:
                return {
                    "tool": "get_article_by_url",
                    "success": False,
                    "error": f"Error HTTP {response.status_code}"
                }
        except Exception as e:
            raise Exception(f"Error en get_article_by_url: {str(e)}")
    
    def _list_categories(self) -> Dict[str, Any]:
        """
        Tool MCP: list_categories
        Endpoint: GET /categories
        """
        try:
            response = requests.get(f"{self.api_url}/categories", timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "tool": "list_categories",
                    "success": True,
                    "total_categories": data["total_categories"],
                    "categories": data["categories"]
                }
            else:
                return {
                    "tool": "list_categories",
                    "success": False,
                    "error": f"Error HTTP {response.status_code}"
                }
        except Exception as e:
            raise Exception(f"Error en list_categories: {str(e)}")
    
    def _get_stats(self) -> Dict[str, Any]:
        """
        Resource MCP: knowledge-base://stats
        Endpoint: GET /stats
        """
        try:
            response = requests.get(f"{self.api_url}/stats", timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "resource": "knowledge-base://stats",
                    "success": True,
                    "stats": data
                }
            else:
                return {
                    "resource": "knowledge-base://stats",
                    "success": False,
                    "error": f"Error HTTP {response.status_code}"
                }
        except Exception as e:
            raise Exception(f"Error en knowledge-base://stats: {str(e)}")
    
    def _extraer_url(self, texto: str) -> str:
        """Extrae URL de un texto usando regex."""
        match = re.search(r'https?://[^\s]+', texto)
        return match.group(0) if match else ""
    
    def _actualizar_memoria(self, pregunta: str, respuesta: Dict[str, Any], intencion: str):
        """
        Actualiza la memoria conversacional del agente.
        
        Memoria corto plazo: Últimos 5 turnos
        Memoria mediano plazo: Temas discutidos
        """
        # Memoria corto plazo
        self.historial_corto.append({
            "pregunta": pregunta,
            "intencion": intencion,
            "tool": respuesta.get("tool") or respuesta.get("resource"),
            "timestamp": datetime.now().isoformat()
        })
        
        # Mantener solo últimos 5 turnos
        if len(self.historial_corto) > 5:
            self.historial_corto.pop(0)
        
        # Memoria mediano plazo: extraer temas
        if respuesta.get("success"):
            if "documents" in respuesta:
                for doc in respuesta["documents"]:
                    self.temas_discutidos.add(doc.get("category", ""))
    
    def get_context(self) -> str:
        """Retorna contexto de la sesión para debugging."""
        return f"""
Sesión iniciada: {self.session_start.strftime('%H:%M:%S')}
Turnos de conversación: {len(self.historial_corto)}
Temas discutidos: {', '.join(self.temas_discutidos) if self.temas_discutidos else 'Ninguno'}
"""


def main():
    """Modo CLI standalone del agente."""
    print("=" * 60)
    print("Asistente Virtual Bancolombia")
    print("=" * 60)
    print("Cliente MCP - Agente Conversacional")
    print("Escribe 'salir' para terminar\n")
    
    agent = BancolombiaAgent()
    
    while True:
        try:
            pregunta = input("\nTu: ").strip()
            
            if not pregunta:
                continue
            
            if pregunta.lower() in ["salir", "exit", "quit"]:
                print("\nHasta luego")
                break
            
            print("\n[Procesando...]")
            respuesta = agent.ask(pregunta)
            
            if respuesta.get("error"):
                print(f"\nError: {respuesta['message']}")
                if "suggestion" in respuesta:
                    print(f"Sugerencia: {respuesta['suggestion']}")
            elif respuesta.get("success"):
                print(f"\nAsistente:")
                
                # Formatear según el tipo de respuesta
                if "documents" in respuesta:
                    print(f"\nEncontré {respuesta['total_results']} documentos relevantes:\n")
                    for doc in respuesta["documents"]:
                        print(f"{doc['rank']}. {doc['title']} (Score: {doc['similarity_score']})")
                        print(f"   Categoría: {doc['category']}")
                        print(f"   {doc['content'][:200]}...")
                        print(f"   Fuente: {doc['url']}\n")
                
                elif "chunks" in respuesta:
                    print(f"\nArtículo: {respuesta['title']}")
                    print(f"Categoría: {respuesta['category']}")
                    print(f"Total chunks: {len(respuesta['chunks'])}\n")
                    for i, chunk in enumerate(respuesta['chunks'][:2], 1):
                        print(f"Chunk {i}:")
                        print(f"{chunk['content'][:300]}...")
                        print()
                
                elif "categories" in respuesta:
                    print(f"\nCategorías disponibles ({respuesta['total_categories']}):\n")
                    for i, cat in enumerate(respuesta['categories'][:10], 1):
                        print(f"{i}. {cat}")
                    if respuesta['total_categories'] > 10:
                        print(f"... y {respuesta['total_categories'] - 10} más")
                
                elif "stats" in respuesta:
                    stats = respuesta['stats']
                    print(f"\nEstadísticas de la base de conocimiento:")
                    print(f"Total documentos: {stats['total_documents']}")
                    print(f"Categorías: {stats['num_categories']}")
                    print(f"Dimensión embeddings: {stats['embedding_dimension']}")
                    print(f"Métrica: {stats['distance_metric']}")
            
        except KeyboardInterrupt:
            print("\n\nHasta luego")
            break
        except Exception as e:
            print(f"\nError inesperado: {str(e)}")


if __name__ == "__main__":
    main()

# Código generado por GitHub Copilot
