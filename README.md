# Thoth Scann

> **Suite inteligente de conversión y digitalización de documentos y código fuente a Markdown estructurado para LLMs y RAG.**  
> *Basado en el motor modular MarkItDown de Microsoft con extensiones avanzadas de código fuente, interfaz web interactiva y procesamiento por lotes.*

---

## Características Principales

* **Soporte Documental Integral**:
  * **PDFs**: Extracción de texto estructurado, tablas con alineación precisa (`pdfplumber` y `pdfminer`) y detección de formularios.
  * **Office**: Word (`.docx`), Excel (`.xlsx`, `.xls`) convertido a tablas Markdown limpias, PowerPoint (`.pptx`).
  * **Contenedores y Libros**: Libros electrónicos (`.epub`), Notebooks (`.ipynb`), archivos `.zip`.
  * **Datos y Web**: CSV, JSON, XML, HTML y descarga directa de páginas web / Wikipedia.

* **Extracción Especializada de Código Fuente y Repositorios**:
  * Reconocimiento y formateo con bloques de resaltado de sintaxis para más de 20 lenguajes:
    * **Java** (`.java`), **R** (`.r`, `.R`), **Python** (`.py`), **Shell/Bash** (`.sh`, `.bash`, `.zsh`).
    * **Configuración**: YAML (`.yml`, `.yaml`), JSON, TOML, XML.
    * **Web y Sistemas**: JavaScript (`.js`, `.ts`, `.tsx`), C/C++ (`.c`, `.cpp`), C#, Rust (`.rs`), Go (`.go`), SQL, `Dockerfile`, `Makefile`.
  * **Ingesta de Proyectos Completos (Carpetas locales o ZIP)**:
    * **TREE.md**: Árbol jerárquico visual ASCII y métricas de código.
    * **Estructura Espejo (`sources/`)**: Archivos separados individuales organizados en subcarpetas para indexación RAG o agentes modulares.
    * **CONSOLIDATED.md**: Archivo todo-en-uno delimitado para LLMs de ventana amplia (Gemini 2.0, Claude 3.7, GPT-4o).
    * **Filtros Inteligentes**: Exclusión automática de ruido (`node_modules`, `.venv`, `.git`, binarios y lockfiles).

* **Capacidades de OCR y Visión Multimodal**:
  * Compatible con modelos de visión (OpenAI GPT-4o o APIs compatibles) para extraer texto de imágenes embebidas o documentos escaneados.
  * Renderizado de páginas escaneadas a 300 DPI con recuperación mediante `PyMuPDF`.

* **Interfaz Gráfica de Usuario (Web UI)**:
  * Construida con **Streamlit**, moderna, rápida e intuitiva.
  * **Pestaña 1 (Individual)**: Carga por Drag & Drop, visor dual y métricas de tokens.
  * **Pestaña 2 (Lotes)**: Procesa múltiples archivos a la vez con barra de progreso y descarga ZIP.
  * **Pestaña 3 (Proyectos / Repositorios)**: Escanea carpetas locales o ZIPs de código con opciones de generación.
  * **Pestaña 4 (Web)**: Conversión directa de URLs a Markdown limpio.
  * **Guardado Automático en Disco**: Cada corrida genera su carpeta organizada dentro de `output/`.

---

## Estructura del Proyecto

```text
thoth_scann/
├── app.py                     # Aplicación web interactiva (Streamlit)
├── run_ui.sh                  # Lanzador rápido de un solo clic para Linux
├── restart_docker.sh          # Script de recreación y despliegue del contenedor
├── Dockerfile                 # Contenedor Docker de producción
├── docker-compose.yml         # Orquestación con volúmenes de salida y red
├── README.md                  # Documentación completa del proyecto
├── output/                    # Directorio de guardado automático de archivos .md
├── thoth_extractor/           # Módulo autónomo de análisis y extracción de proyectos
│   ├── __init__.py
│   └── project_extractor.py
├── tests/                     # Suite de pruebas unitarias
│   └── test_project_extractor.py
└── markitdown-main/           # Motor base desacoplado y modular
    └── packages/
        ├── markitdown/        # Núcleo y CLI de MarkItDown
        ├── markitdown-ocr/    # Plugin de OCR vía LLM Vision
        ├── markitdown-mcp/    # Servidor Model Context Protocol para IA
        └── markitdown-sample-plugin/ # Ejemplo de extensibilidad
```

---

## Requisitos e Instalación

### Requisitos Previos
* **Linux / macOS / Windows**
* **Python 3.10 o superior**
* **Docker y Docker Compose (opcional para despliegue en contenedor)**

### Instalación Rápida

1. **Clonar o descomprimir el proyecto**:
   ```bash
   cd thoth_scann
   ```

2. **Crear y activar el entorno virtual**:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. **Instalar el motor y dependencias de documentos**:
   ```bash
   pip install --upgrade pip
   pip install -e './markitdown-main/packages/markitdown'
   pip install pdfminer.six pdfplumber mammoth python-docx openpyxl pandas python-pptx
   pip install streamlit
   ```

4. *(Opcional)* Si deseas habilitar OCR con modelos de visión LLM:
   ```bash
   pip install -e './markitdown-main/packages/markitdown-ocr'
   pip install openai
   ```

---

## Modo de Uso

### 1. Iniciar la Interfaz Gráfica (Recomendado)

Simplemente ejecuta el script lanzador:
```bash
./run_ui.sh
```

O si prefieres el comando directo con el entorno virtual activo:
```bash
streamlit run app.py
```

Abre tu navegador en: **`http://localhost:8501`**

### 2. Uso con Docker

Para reconstruir y levantar la aplicación en contenedor:
```bash
./restart_docker.sh
```

### 3. Uso por Línea de Comandos (CLI)

```bash
# Convertir un PDF o Word a Markdown en consola
markitdown documento.pdf

# Guardar la salida en un archivo
markitdown informe.docx -o informe.md

# Convertir un archivo Excel con tablas
markitdown datos.xlsx -o datos.md

# Usar tuberías (pipes)
cat archivo.pdf | markitdown > salida.md
```

### 4. Uso como Librería en Python

```python
from markitdown import MarkItDown

md = MarkItDown()
resultado = md.convert("documento.pdf")
print(resultado.markdown)
```

---

## Dónde se Guardan los Archivos

1. **Automático en disco**: En la carpeta `thoth_scann/output/` se almacena una copia con el mismo nombre y extensión `.md`. Puedes cambiar esta ruta o desactivarlo desde la barra lateral de la interfaz.
2. **Descarga en navegador**: Con los botones **"Descargar Markdown (.md)"** o el archivo `.zip` en lotes, se guardarán en tu carpeta habitual de descargas (`~/Descargas`).

---

## Licencia y Créditos

* Este proyecto utiliza y extiende el software de código abierto **MarkItDown** desarrollado por Microsoft bajo licencia **MIT**.
* Libre para uso personal, comercial, modificación y distribución.
