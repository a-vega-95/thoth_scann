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

## Resultados de Verificación
- **Escaneo de Emojis/Símbolos**: 0 caracteres residuales en archivos fuente, UI, scripts y documentación.
- **Pruebas Unitarias**: `tests/test_project_extractor.py` ejecutado y aprobado al 100% (carpetas y ZIPs).
- **Compilación Python**: `py_compile` ejecutado exitosamente en todos los módulos (`app.py`, `thoth_extractor`, `tests`).
- **Prueba de Servidor Headless**: Servidor Streamlit inicializado y validado en puerto de prueba sin advertencias.
- **Empaquetado**: Archivo `thoth_scann_dist.zip` reconstruido y sincronizado.
