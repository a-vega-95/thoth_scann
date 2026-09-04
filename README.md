# 📜 Thoth Scann

> **Suite inteligente de conversión y digitalización de documentos y código fuente a Markdown estructurado para LLMs y RAG.**  
> *Basado en el motor modular MarkItDown de Microsoft con extensiones avanzadas de código fuente, interfaz web interactiva y procesamiento por lotes.*

---

## 🌟 Características Principales

* **📄 Soporte Documental Integral**:
  * **PDFs**: Extracción de texto estructurado, tablas con alineación precisa (`pdfplumber` y `pdfminer`) y detección de formularios.
  * **Office**: Word (`.docx`), Excel (`.xlsx`, `.xls`) convertido a tablas Markdown limpias, PowerPoint (`.pptx`).
  * **Contenedores y Libros**: Libros electrónicos (`.epub`), Notebooks (`.ipynb`), archivos `.zip`.
  * **Datos y Web**: CSV, JSON, XML, HTML y descarga directa de páginas web / Wikipedia.

* **💻 Extracción Especializada de Código Fuente y Repositorios**:
  * Reconocimiento y formateo con bloques de resaltado de sintaxis para más de 20 lenguajes:
    * **Java** (`.java`), **R** (`.r`, `.R`), **Python** (`.py`), **Shell/Bash** (`.sh`, `.bash`, `.zsh`).
    * **Configuración**: YAML (`.yml`, `.yaml`), JSON, TOML, XML.
    * **Web y Sistemas**: JavaScript (`.js`, `.ts`, `.tsx`), C/C++ (`.c`, `.cpp`), C#, Rust (`.rs`), Go (`.go`), SQL, `Dockerfile`, `Makefile`.
  * **Ingesta de Proyectos en ZIP**: Sube un archivo `.zip` con un repositorio o carpeta de software completo y Thoth Scann extraerá, organizará y documentará todos los scripts en un único archivo Markdown consolidado listo para alimentar modelos de lenguaje.

* **👁️ Capacidades de OCR y Visión Multimodal**:
  * Compatible con modelos de visión (OpenAI GPT-4o o APIs compatibles) para extraer texto de imágenes embebidas o documentos escaneados.
  * Renderizado de páginas escaneadas a 300 DPI con recuperación mediante `PyMuPDF`.

* **🖥️ Interfaz Gráfica de Usuario (Web UI)**:
  * Construida con **Streamlit**, moderna, rápida e intuitiva.
  * **Pestaña Individual**: Carga por arrastrar y soltar (Drag & Drop), visor dual (Markdown renderizado vs Código fuente raw) y métricas de palabras, caracteres y estimación de tokens LLM.
  * **Pestaña por Lotes (Batch)**: Procesa múltiples archivos a la vez con barra de progreso y descarga consolidada en `.zip`.
  * **Pestaña Web**: Conversión directa de URLs a Markdown limpio sin anuncios ni código residual.
  * **💾 Guardado Automático en Disco**: Cada archivo procesado se guarda automáticamente en la carpeta `output/` de forma organizada.

---

## 📂 Estructura del Proyecto

```text
thoth_scann/
├── app.py                     # Aplicación web interactiva (Streamlit)
├── run_ui.sh                  # Lanzador rápido de un solo clic para Linux
├── README.md                  # Documentación del proyecto
├── output/                    # Directorio de guardado automático de archivos .md
└── markitdown-main/           # Motor base desacoplado y modular
    └── packages/
        ├── markitdown/        # Núcleo y CLI de MarkItDown
        ├── markitdown-ocr/    # Plugin de OCR vía LLM Vision
        ├── markitdown-mcp/    # Servidor Model Context Protocol para IA
        └── markitdown-sample-plugin/ # Ejemplo de extensibilidad
```

---

## 🚀 Requisitos e Instalación

### Requisitos Previos
* **Linux / macOS / Windows**
* **Python 3.10 o superior**

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

## 🎯 Modo de Uso

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

### 2. Uso por Línea de Comandos (CLI)

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

### 3. Uso como Librería en Python

```python
from markitdown import MarkItDown

md = MarkItDown()
resultado = md.convert("documento.pdf")
print(resultado.markdown)
```

---

## 💾 Dónde se Guardan los Archivos

1. **Automático en disco**: En la carpeta `thoth_scann/output/` se almacena una copia con el mismo nombre y extensión `.md`. Puedes cambiar esta ruta o desactivarlo desde la barra lateral de la interfaz.
2. **Descarga en navegador**: Con los botones **"📥 Descargar .md"** o el archivo `.zip` en lotes, se guardarán en tu carpeta habitual de descargas (`~/Descargas`).

---

## 🛡️ Licencia y Créditos

* Este proyecto utiliza y extiende el software de código abierto **MarkItDown** desarrollado por Microsoft bajo licencia **MIT**.
* Libre para uso personal, comercial, modificación y distribución.
# thoth_scann
