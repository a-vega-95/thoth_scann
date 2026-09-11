# Plan de Tareas: Implementación de Interfaz Limpia y Profesional

## Objetivo
Refactorizar y transformar la interfaz de usuario, scripts auxiliares, motor de extracción y documentación de **Thoth Scann** hacia un estándar de diseño sobrio, formal y corporativo, eliminando el uso de emojis informales y garantizando máxima compatibilidad técnica y elegancia visual.

---

## Especificación de Cambios

1. **`app.py` (UI Streamlit)**:
   - Configuración de página: icono neutral/formal (ej. `"DOCUMENT"` o icono corporativo sin emoji decorativo).
   - Títulos y cabeceras: estilo sobrio (`Thoth Scann | Digital Document & Code Converter`).
   - Pestañas principales:
     - De `"📄 Documento Individual"` -> `"Documento Individual"`
     - De `"📦 Procesamiento por Lotes"` -> `"Procesamiento por Lotes"`
     - De `"📂 Repositorio / Proyecto de Software"` -> `"Repositorio / Proyecto"`
     - De `"🌐 Convertir desde URL"` -> `"Conversión Web / URL"`
   - Subpestañas:
     - De `"👁️ Vista Renderizada"` -> `"Vista Previa"`
     - De `"💻 Código Markdown (Raw)"` -> `"Código Markdown (Fuente)"`
     - De `"🌳 Mapa del Proyecto (TREE.md)"` -> `"Mapa de Directorios (TREE.md)"`
     - De `"📊 Desglose de Lenguajes"` -> `"Distribución de Lenguajes"`
   - Botones y alertas:
     - De `"⚡ Convertir a Markdown"` -> `"Convertir a Markdown"`
     - De `"📥 Descargar .md"` -> `"Descargar Markdown (.md)"`
     - De `"❌ Error..."` -> `"Error: ..."`
     - De `"✅ Conversión completada..."` -> `"Conversión completada con éxito."`
     - De `"💾 Copia guardada en disco:"` -> `"Archivo guardado en disco:"`
   - Barra lateral:
     - Ajustes de motor, OCR y directorios con títulos limpios y claros.

2. **`thoth_extractor/project_extractor.py`**:
   - Plantilla de `TREE.md`:
     - De `# 🗺️ Mapa Arquitectónico...` -> `# Estructura Arquitectónica: ...`
     - De `## 📊 Métricas Generales` -> `## Métricas del Proyecto`
     - De `## 💻 Desglose por Lenguaje` -> `## Distribución de Lenguajes`
     - De `## 🌳 Árbol Jerárquico...` -> `## Árbol de Directorios`
     - De `## 📑 Índice de Archivos...` -> `## Catálogo de Archivos Fuente`
   - Encabezado de `CONSOLIDATED.md`: texto descriptivo formal sin emojis.

3. **Scripts de Shell (`run_ui.sh`, `restart_docker.sh`)**:
   - Eliminar emojis en los mensajes `echo`, sustituyéndolos por prefijos formales como `[INFO]`, `[OK]`, `[AVISO]`.

4. **Documentación (`README.md`)**:
   - Reemplazar emojis en encabezados y listas por viñetas limpias y títulos formales.

---

## Lista de Tareas Verificables

- [x] **Fase 1: Refactorización de `app.py`**
  - [x] Reemplazar emojis en títulos, sidebar y pestañas.
  - [x] Reemplazar emojis en botones, subpestañas, métricas y mensajes de notificación.
  - [x] Pulir estilos CSS para una apariencia corporativa elegante.
- [x] **Fase 2: Refactorización de `thoth_extractor/project_extractor.py`**
  - [x] Actualizar encabezados y tablas en las plantillas de `TREE.md` y `CONSOLIDATED.md`.
  - [x] Ejecutar prueba unitaria para validar que las aserciones sigan cumpliéndose.
- [x] **Fase 3: Refactorización de Scripts y Documentación**
  - [x] Limpiar `run_ui.sh` y `restart_docker.sh`.
  - [x] Actualizar `README.md` a estilo formal.
- [x] **Fase 4: Verificación Integral**
  - [x] Comprobar que ningún archivo de código o UI contenga emojis no deseados.
  - [x] Ejecutar `python -m py_compile app.py thoth_extractor/project_extractor.py`.
  - [x] Ejecutar prueba de arranque de Streamlit en modo headless.
  - [x] Reconstruir archivo de distribución `thoth_scann_dist.zip`.

---

## Resultados de Verificación (Fase Previa)
- **Escaneo de Emojis/Símbolos**: 0 caracteres residuales en archivos fuente, UI, scripts y documentación.
- **Pruebas Unitarias**: `tests/test_project_extractor.py` ejecutado y aprobado al 100% (carpetas y ZIPs).
- **Compilación Python**: `py_compile` ejecutado exitosamente en todos los módulos (`app.py`, `thoth_extractor`, `tests`).
- **Prueba de Servidor Headless**: Servidor Streamlit inicializado y validado en puerto de prueba sin advertencias.
- **Empaquetado**: Archivo `thoth_scann_dist.zip` reconstruido y sincronizado.

---

# Plan de Trabajo: Creación de Versión de Escritorio Portable (Standalone Runtime Bundle)

## Objetivo
Construir y verificar una distribución de escritorio 100% portable y autocontenida de **Thoth Scann** para sistemas Linux x86_64, basada en el estándar industrial `python-build-standalone` (Astral), sin requerir Docker, Python instalado ni privilegios de administrador (`sudo`).

## Especificaciones de Arquitectura
1. **Intérprete Autónomo**: CPython 3.12 x86_64 stripped (glibc compatible).
2. **Dependencias Preinstaladas**: Streamlit, MarkItDown, pdfminer.six, pdfplumber, mammoth, openpyxl, pandas, python-docx, python-pptx, etc.
3. **Invocación Relativa**: Uso de `$HERE/runtime/bin/python3 -m streamlit run app.py` para evitar rotura por shebangs con rutas absolutas.
4. **Lanzadores**:
   - `thoth_scann.sh`: Script ejecutable con detección automática de ruta y navegador.
   - `thoth-scann.desktop`: Acceso directo para integración en entornos de escritorio Linux.
5. **Empaquetado Final**: Generación de `thoth_scann_portable_linux_x86_64.tar.gz` listo para distribución.

## Lista de Tareas Verificables
- [x] **Paso 1: Descarga y Extracción del Runtime de Python Standalone**
  - [x] Descargar `cpython-3.12.*-x86_64-unknown-linux-gnu-install_only_stripped.tar.gz`.
  - [x] Extraer en directorio temporal y verificar ejecución del binario `python3 --version`.
- [x] **Paso 2: Instalación de Dependencias en el Runtime Aislado**
  - [x] Actualizar pip e instalar paquetes de `requirements.txt`.
  - [x] Instalar el paquete local `markitdown`.
- [x] **Paso 3: Estructuración del Bundle Portable**
  - [x] Copiar código fuente limpio (`app.py`, `thoth_extractor/`, plantillas y configuración).
  - [x] Crear directorio de persistencia `output/`.
  - [x] Crear script lanzador `thoth_scann.sh` con manejo de rutas relativas y apertura de navegador.
  - [x] Crear archivo `.desktop` y `README_PORTABLE.md`.
- [x] **Paso 4: Pruebas de Portabilidad y Aislamiento**
  - [x] Probar ejecución del bundle desde una ruta arbitraria fuera del repo original (`/tmp/thoth_portable_test`).
  - [x] Validar importación de todas las dependencias con el Python del bundle.
  - [x] Validar que la interfaz web arranque correctamente.
- [x] **Paso 5: Compresión y Distribución**
  - [x] Generar archivo final comprimido `thoth_scann_portable_linux_x86_64.tar.gz`.
  - [x] Documentar el uso para el usuario final.

---

## Resultados de la Fase de Portabilidad
- **Runtime Embebido**: CPython 3.12.14 x86_64 stripped (glibc 2.28+ compatible).
- **Aislamiento**: Verificado en directorio `/tmp` externo; `$HERE/runtime/bin/python3` ejecuta Streamlit y módulos dependientes sin rutas codificadas en duro.
- **Dinamismo de Rutas**: `app.py` y `project_extractor.py` actualizados para resolver automáticamente su ruta base `BASE_DIR` y subdirectorio local `output/`.
- **Paquete de Distribución**: Generado exitosamente en `/home/massive-usr/Documentos/desarrollo/thoth_scann_portable_linux_x86_64.tar.gz` (203 MB comprimido).

---

# Plan de Trabajo: Optimización de Extracción .MD, Catálogo Completo de Formatos y Módulo Web/URL

## Objetivos
1. **Desactivar la carga automática de vista previa pesada** para acelerar la extracción a .MD, eliminando cuellos de botella de renderizado en DOM/Streamlit.
2. **Rediseñar y expandir el catálogo visual de Formatos Soportados** con una lista exhaustiva, categorizada y profesional de todos los formatos procesables.
3. **Robustecer y auditar el módulo de Conversión Web / URL**: normalización de esquemas (http/https), sesión HTTP resiliente con User-Agent moderno, headers anti-bloqueo, control de timeouts y manejo exhaustivo de excepciones.

## Lista de Tareas Verificables
- [x] **Paso 1: Optimización del Pipeline y Eliminación de Vista Previa Pesada**
  - [x] En Documento Individual (Pestaña 1): reemplazar la carga obligatoria de `st.markdown()` y `st.code()` por tarjeta de métricas instantánea, botón de descarga directa y un expander colapsado opcional bajo demanda.
  - [x] En Repositorio / Proyecto (Pestaña 3): evitar cargar `CONSOLIDATED.md` completo en `st.text_area()`, ofreciendo descarga directa y muestra bajo demanda para prevenir congelamientos de navegador.
  - [x] En Conversión Web (Pestaña 4): desactivar renderizado masivo automático y ofrecer métricas inmediatas con muestra opcional.
- [x] **Paso 2: Rediseño Visual y Catálogo Completo de Formatos Soportados**
  - [x] Reestructurar la sección de la barra lateral con tarjetas visuales y categorías claras.
  - [x] Agregar catálogo completo y exhaustivo: Documentos (PDF, DOCX, XLSX, XLS, PPTX, EPUB, RTF), Código (20+ lenguajes, frameworks, Dockerfile, Makefile), Datos (CSV, JSON, TOML, XML, TXT, LOG), Multimedia (JPG, PNG, MP3, WAV con OCR/metadatos), Contenedores (ZIP, Repositorios) y Web (HTML, Wikipedia).
- [x] **Paso 3: Robustecimiento Integral del Módulo Web / URL**
  - [x] Configurar `requests.Session()` con `User-Agent` de navegador moderno, `Accept`, `Accept-Language` y timeout de seguridad.
  - [x] Normalizar URLs entrantes (anteponer `https://` si el usuario omite el protocolo).
  - [x] Capturar errores de red específicos (`ConnectionError`, `Timeout`, `HTTPError`, `InvalidURL`) con mensajes descriptivos.
- [x] **Paso 4: Verificación Integral**
  - [x] Ejecutar comprobación de sintaxis con `py_compile`.
  - [x] Probar extracción web con URLs reales (Wikipedia, sitios HTML estándar) y verificar tiempos de respuesta.
  - [x] Probar extracción de documentos sin carga de vista previa y comprobar velocidad.
  - [x] Actualizar paquetes distribuibles (`thoth_scann_dist.zip` y `thoth_scann_portable_linux_x86_64.tar.gz`).

---

## Resultados de la Fase de Optimización
- **Rendimiento UI**: La vista previa automática pesada fue eliminada en todas las pestañas; el DOM de Streamlit ahora responde de manera instantánea, dejando la muestra como opción colapsada bajo demanda.
- **Catálogo de Formatos**: Barra lateral rediseñada con badges visuales agrupados y tabla técnica detallada de capacidades de extracción.
- **Módulo Web / URL**: Probado y operativo con User-Agent de Chrome de escritorio, encabezados multilingües, normalización de esquemas y captura robusta de excepciones de red.
- **Distribución**: Ambas versiones portables actualizadas y sincronizadas con las últimas mejoras.

---

# Plan de Trabajo: División de Documentos Extensos con Preservación de Contexto para IA / IAG

## Objetivos
1. **Módulo de División Inteligente (`thoth_extractor/document_splitter.py`)**:
   - Algoritmo de particionado respetuoso con la sintaxis Markdown (no corta en medio de bloques de código ni párrafos).
   - Estrategias de división: Por Tokens de contexto (LLM), Por Número fijo de partes, y Por Encabezados/Capítulos.
   - Generación de metadatos de contexto de nivel empresarial:
     - **YAML Frontmatter**: `document_id`, `part`, `total_parts`, `next_part`, `previous_part`, `tokens`, `topics`.
     - **Banner de Continuidad Semántica**: Directivas claras de navegación e ingesta para LLMs/RAG.
     - **Pie de Página de Continuidad**: Enlace al fragmento siguiente.
     - **Índice Maestro (`<documento>_INDEX.md`)**: Manifiesto con catálogo de partes, métricas y árbol temático.
   - Generador de paquetes ZIP en memoria y guardado en disco estructurado.
2. **Integración Exclusiva en Tab 1 (Documento Individual)**:
   - Controles limpios y formales para activar la división de documentos.
   - Selector de estrategia (tokens, partes, encabezados) y controles de configuración.
   - Checkbox de inyección de contexto IA (activo por defecto).
   - Métricas comparativas globales vs fragmentadas.
   - Descarga directa en ZIP de todas las partes + Índice maestro.
   - Guardado automático en subcarpeta dedicada `output/<documento>_partes/`.
3. **Pruebas Unitarias Exhaustivas**:
   - `tests/test_document_splitter.py` validando todas las estrategias, frontmatter y generación de ZIP.
4. **Respuesta Arquitectónica al Usuario**:
   - Explicación fundamentada del estándar de preservación de contexto en sistemas LLM/RAG y agentes AGI.

## Lista de Tareas Verificables
- [x] **Paso 1: Implementación de `thoth_extractor/document_splitter.py`**
  - [x] Implementar clases `SplitOptions`, `DocumentPart`, `SplitResult`, `DocumentSplitter`.
  - [x] Implementar preservación de límites Markdown (evitar fracturar bloques de código y párrafos).
  - [x] Implementar inyección de YAML Frontmatter, banner de contexto y pie de continuidad.
  - [x] Implementar generador de archivo `<documento>_INDEX.md` y empaquetado ZIP.
  - [x] Exportar clases en `thoth_extractor/__init__.py`.
- [x] **Paso 2: Pruebas Unitarias**
  - [x] Crear `tests/test_document_splitter.py`.
  - [x] Probar división por tokens, por número de partes y por encabezados.
  - [x] Validar frontmatter, banners y enlaces entre partes.
  - [x] Ejecutar suite de pruebas de particionado con éxito al 100%.
- [x] **Paso 3: Integración en `app.py` (Tab 1: Documento Individual)**
  - [x] Agregar controles de configuración de división en la columna de opciones de Tab 1.
  - [x] Conectar la lógica de conversión con `DocumentSplitter`.
  - [x] Presentar métricas detalladas por partes y descarga de archivo ZIP + Índice.
  - [x] Guardar en disco estructurado si `auto_save` está activo.
- [x] **Paso 4: Verificación Integral y Distribución**
  - [x] Validar sintaxis con `py_compile`.
  - [x] Ejecutar suite completa de tests unitarios (`tests/test_document_splitter.py` y `tests/test_project_extractor.py`).
  - [x] Actualizar paquetes portables (`thoth_scann_dist.zip` y bundle standalone `thoth_scann_portable_linux_x86_64.tar.gz`).

---

## Resultados de la Fase de Particionado y Contexto para IA
- **Módulo `document_splitter.py`**: Implementado y verificado con 3 estrategias (Por Tokens, Por Partes y Por Encabezados), algoritmo de bloques atómicos que resguarda bloques de código (```...```) y tablas.
- **Contexto IA / IAG Estandarizado**: Cada fragmento generado cuenta con:
  1. YAML Frontmatter (`document_id`, `part`, `total_parts`, `previous_part`, `next_part`, `master_index`, `part_tokens_estimate`, `topics_covered`).
  2. Banner de navegación y continuidad semántica.
  3. Pie de página de enlace secuencial.
  4. Archivo maestro `<documento>_INDEX.md` con manifiesto arquitectónico y catálogo temático completo.
- **Interfaz Streamlit (Tab 1 Exclusiva)**: Controles en acordeón colapsable con sliders de tokens/partes y selector de encabezados. Métricas instantáneas de partes y tokens promedio, descarga ZIP integral con un clic y descargas individuales.
- **Distribución Sincronizada**: Ambos paquetes portables (`thoth_scann_dist.zip` y `thoth_scann_portable_linux_x86_64.tar.gz`) actualizados.


