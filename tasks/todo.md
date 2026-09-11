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
