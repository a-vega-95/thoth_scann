# 📋 Plan de Tareas: Módulo de Extracción de Proyectos y Repositorios

## 🎯 Objetivo
Implementar una solución de nivel profesional dentro de **Thoth Scann** para extraer proyectos de software y repositorios completos (soporte para .java, .R, .py, .sh, .yml, .sql, etc.). El sistema debe:
1. Generar un **`TREE.md`** con la representación visual jerárquica del proyecto y métricas contextuales.
2. Generar archivos individuales estructurados en **carpeta espejo** (óptimo para RAG, indexación y agentes modulares).
3. Generar un **`CONSOLIDATED.md`** opcional con delimitadores precisos (óptimo para LLMs de contexto largo como Gemini 2.0 / Claude 3.7).
4. Soportar tanto **rutas de carpetas locales en disco** (sin carga pesada de navegador) como **archivos `.zip`**.

---

## 📐 Especificación Arquitectónica

### Componente 1: `thoth_extractor/project_extractor.py` (Módulo Autónomo)
* **Clase `ProjectExtractor`**:
  * `scan_directory(path, options) -> ExtractionResult`
  * `scan_zip(zip_bytes_or_path, options) -> ExtractionResult`
* **Módulos Internos**:
  * `FilterEngine`: Parser de `.gitignore` + lista de exclusiones por defecto (`node_modules`, `.venv`, `.git`, `target`, `dist`, binarios, lockfiles).
  * `TreeBuilder`: Generador de árbol ASCII jerárquico y cálculo de estadísticas (archivos, líneas, conteo de tokens aproximado, distribución de lenguajes).
  * `CodeFormatter`: Formateador Markdown que envuelve cada archivo con sintaxis resaltada y metadatos de ruta relativa.
  * `OutputWriter`: Escritura en disco de `TREE.md`, carpeta espejo `sources/`, y `CONSOLIDATED.md`.

### Componente 2: Integración en `app.py` (Streamlit UI)
* Pestaña dedicada: **"📂 Repositorio / Proyecto de Software"**.
* Controles:
  * Selector de entrada: "📁 Carpeta Local en Disco" vs "📦 Archivo ZIP".
  * Casillas de configuración:
    * `[x] Generar archivos separados (Espejo para RAG)`
    * `[x] Generar archivo consolidado único (Para chats LLM)`
    * `[x] Generar mapa contextual TREE.md`
    * Selector de extensiones a incluir/excluir.
  * Visualización en tiempo real:
    * Métricas de resumen (Archivos procesados, Lenguajes, Líneas de código, Tokens estimados).
    * Vista previa interactiva del `TREE.md` y del `CONSOLIDATED.md`.
    * Botón de descarga ZIP consolidado y botón de apertura de carpeta de salida.

---

## 📋 Lista de Tareas Verificables

- [x] **Fase 1: Módulo Core de Extracción (`thoth_extractor/`)**
  - [x] Diseñar `thoth_extractor/project_extractor.py` desacoplado de la UI.
  - [x] Implementar algoritmo de árbol ASCII y estadísticas de lenguajes.
  - [x] Implementar filtrado de exclusiones (.git, .venv, node_modules, etc.).
  - [x] Implementar generador de `TREE.md`, carpeta espejo de fuentes y `CONSOLIDATED.md`.
- [x] **Fase 2: Pruebas y Verificación del Motor Core**
  - [x] Crear un proyecto sintético de prueba con múltiples lenguajes (.java, .py, .r, .sh, .yml).
  - [x] Ejecutar script de prueba autónomo y verificar que se generen correctamente los 3 formatos.
  - [x] Validar que se respeten exclusiones y que las rutas relativas sean exactas.
- [x] **Fase 3: Integración en la Interfaz Gráfica (`app.py`)**
  - [x] Incorporar la pestaña "📂 Proyecto / Repositorio Completo".
  - [x] Conectar selector de ruta local y uploader de archivo `.zip`.
  - [x] Añadir controles de generación (Espejo vs Consolidado vs Tree).
  - [x] Mostrar métricas, vista previa y descarga.
- [x] **Fase 4: Verificación Integral del Sistema**
  - [x] Comprobar compilación y ejecución de `app.py` sin errores ni advertencias.
  - [x] Probar la interfaz end-to-end con una carpeta real.
  - [x] Actualizar documentación en `README.md` y documentar resultados en `tasks/todo.md`.
  - [x] Recrear el ZIP de distribución `thoth_scann_dist.zip`.

---

## 🔬 Resultados de Verificación y Demostración

1. **Pruebas Unitarias Automatizadas**:
   - `tests/test_project_extractor.py` ejecutado con éxito.
   - Verificó:
     - Detección de múltiples lenguajes (`.java`, `.py`, `.r`, `.sh`, `.yml`).
     - Filtrado estricto de carpetas ignoradas (`node_modules`, `.venv`, `.git`) y lockfiles (`package-lock.json`).
     - Creación y contenido de `TREE.md`, `CONSOLIDATED.md` y carpeta espejo `sources/`.
     - Extracción idéntica desde carpeta local y desde buffer ZIP en memoria.

2. **Prueba End-to-End en Entorno Real**:
   - Ejecución de extracción sobre `markitdown-sample-plugin`.
   - Resultado: 9 archivos procesados, ~15,089 tokens estimados, `TREE.md` y `CONSOLIDATED.md` generados correctamente en disco.

3. **Verificación de la Interfaz Web**:
   - Compilación con `py_compile` limpia (código de salida 0).
   - Arranque de Streamlit en modo headless exitoso (puerto 8501, Uvicorn started).
