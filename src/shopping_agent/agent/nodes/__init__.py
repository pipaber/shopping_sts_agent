"""Nodos del grafo, por grupos: la conversación (``turn``), las acciones que
propone el LLM (``actions``) y el cierre de la compra (``checkout``).

Cada nodo es una función que recibe el estado y devuelve lo que cambia. Los que
eligen a dónde va el grafo devuelven ``Command(update=..., goto=...)`` y declaran
sus destinos en el tipo de retorno; los que tienen un único destino devuelven solo
los cambios. Las dependencias externas llegan en el argumento ``deps``.
"""
