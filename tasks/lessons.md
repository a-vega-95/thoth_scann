# 🧠 Lecciones Aprendidas y Reglas de Calidad (Thoth Scann)

Este archivo registra las lecciones aprendidas, patrones detectados y reglas preventivas para garantizar la máxima calidad en el desarrollo de Thoth Scann.

---

## 📌 Reglas de Calidad del Código

1. **Arquitectura Limpia y Desacoplada**:
   - Separar siempre la lógica de procesamiento (backend/core) de la capa de presentación (Streamlit UI).
   - El motor de extracción debe ser una librería autónoma importable mediante CLI o script, sin depender de Streamlit para funcionar.

2. **Manejo de Archivos y Streams**:
   - No asumir codificación UTF-8 universal: aplicar detección de charset (`charset-normalizer`) y fallback con reemplazo seguro de caracteres (`errors='replace'`).
   - Respetar siempre los punteros de lectura (`seek(0)`) al manipular flujos de bytes.

3. **Optimización de Contexto para LLMs**:
   - Evitar ruido en el árbol y volcado: omitir estrictamente binarios, artefactos de compilación (`.pyc`, `.class`, `.o`), dependencias externas (`node_modules`, `.venv`) y lockfiles masivos.
   - Proveer siempre el árbol ASCII antes del contenido de los archivos para que el LLM pueda mapear dependencias relativas antes de procesar el código.

4. **Estándar de Interfaz Profesional y Empresarial**:
   - Evitar el uso de emojis informales en interfaces de usuario, botones, pestañas, scripts de shell, logs y reportes generados.
   - Utilizar tipografía limpia, etiquetas semánticas claras y convenciones estándar de software profesional para maximizar la legibilidad y evitar problemas de codificación (`charmap`/`cp1252`) en entornos heterogéneos.

5. **Verificación Sistemática**:
   - Cada nueva funcionalidad debe ser verificada con un script de prueba automatizado y validación de tipos/sintaxis antes de considerarse completa.
