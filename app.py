"""
Thoth Scann - Interfaz Gráfica de Usuario (UI)
Conversión inteligente de documentos a Markdown estructurado para LLMs y análisis documental.
Basado en el motor MarkItDown.
"""

import io
import os
import re
import sys
import time
import zipfile
from pathlib import Path
from urllib.parse import urlparse
import requests
import streamlit as st

# Directorio raíz base de la aplicación y ruta por defecto de salida
BASE_DIR = Path(__file__).resolve().parent
DEFAULT_OUTPUT_DIR = str(BASE_DIR / "output")

# Importación del motor MarkItDown y Thoth Extractor
sys.path.insert(0, str(BASE_DIR))
try:
    from markitdown import MarkItDown, StreamInfo
    from thoth_extractor import (
        extract_directory,
        extract_zip,
        ExtractionOptions,
        ExtractionResult,
        DocumentSplitter,
        SplitOptions,
        SplitResult,
    )
except ImportError as e:
    st.error(
        f"Error al importar dependencias del sistema: {e}. "
        "Asegúrate de haber activado el entorno virtual (.venv)."
    )
    st.stop()


# Configuración de página
st.set_page_config(
    page_title="Thoth Scann | Conversor Documental",
    page_icon=None,
    layout="wide",
    initial_sidebar_state="expanded",
)

# Estilos CSS personalizados para una estética limpia y profesional
st.markdown(
    """
    <style>
    .main-title {
        font-size: 2.2rem;
        font-weight: 700;
        color: #1E293B;
        margin-bottom: 0.2rem;
    }
    .subtitle {
        font-size: 1.05rem;
        color: #64748B;
        margin-bottom: 1.5rem;
    }
    .metric-card {
        background-color: #F8FAFC;
        border-radius: 8px;
        padding: 12px;
        border: 1px solid #E2E8F0;
    }
    .stDownloadButton > button {
        background-color: #2563EB !important;
        color: white !important;
        border-radius: 6px !important;
        font-weight: 600 !important;
    }
    .format-pill {
        display: inline-block;
        background-color: #F1F5F9;
        color: #334155;
        border: 1px solid #CBD5E1;
        border-radius: 4px;
        padding: 2px 6px;
        font-size: 0.74rem;
        font-family: monospace;
        font-weight: 500;
        margin: 1px 2px;
    }
    .format-cat {
        font-weight: 600;
        color: #0F172A;
        font-size: 0.82rem;
        margin-top: 8px;
        margin-bottom: 3px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def format_bytes(size_bytes: int) -> str:
    """Convierte bytes a formato legible (KB, MB)."""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    else:
        return f"{size_bytes / (1024 * 1024):.2f} MB"


# Diccionario de extensiones de código a lenguajes Markdown
CODE_EXTENSIONS = {
    ".py": "python",
    ".java": "java",
    ".r": "r",
    ".sh": "bash",
    ".bash": "bash",
    ".zsh": "bash",
    ".yml": "yaml",
    ".yaml": "yaml",
    ".json": "json",
    ".js": "javascript",
    ".mjs": "javascript",
    ".cjs": "javascript",
    ".ts": "typescript",
    ".tsx": "tsx",
    ".jsx": "jsx",
    ".c": "c",
    ".cpp": "cpp",
    ".cc": "cpp",
    ".cxx": "cpp",
    ".h": "c",
    ".hpp": "cpp",
    ".cs": "csharp",
    ".go": "go",
    ".rs": "rust",
    ".php": "php",
    ".rb": "ruby",
    ".sql": "sql",
    ".html": "html",
    ".css": "css",
    ".scss": "scss",
    ".xml": "xml",
    ".toml": "toml",
    ".ini": "ini",
    ".kt": "kotlin",
    ".scala": "scala",
    ".dart": "dart",
    ".swift": "swift",
    ".lua": "lua",
    ".dockerfile": "dockerfile",
}


class SourceCodeConverter:
    """Convertidor especializado para código fuente con resaltado de sintaxis."""

    def accepts(self, file_stream, stream_info, **kwargs) -> bool:
        ext = (stream_info.extension or "").lower()
        fname = (stream_info.filename or "").lower()
        if ext in CODE_EXTENSIONS:
            return True
        if fname in ("dockerfile", "makefile", "cmakelists.txt", "jenkinsfile"):
            return True
        return False

    def convert(self, file_stream, stream_info, **kwargs):
        from markitdown import DocumentConverterResult

        ext = (stream_info.extension or "").lower()
        fname = stream_info.filename or "código"
        lang = CODE_EXTENSIONS.get(ext, "")
        if fname.lower() == "dockerfile":
            lang = "dockerfile"
        elif fname.lower() == "makefile":
            lang = "makefile"

        raw = file_stream.read()
        try:
            content = raw.decode(stream_info.charset or "utf-8")
        except UnicodeDecodeError:
            try:
                import charset_normalizer

                content = str(
                    charset_normalizer.from_bytes(raw).best()
                    or raw.decode("latin-1", errors="replace")
                )
            except Exception:
                content = raw.decode("latin-1", errors="replace")

        md = f"### `{fname}`\n```{lang}\n{content}\n```\n"
        return DocumentConverterResult(markdown=md, title=fname)


def get_markitdown_instance(
    enable_plugins: bool = False,
    openai_api_key: str = "",
    llm_model: str = "gpt-4o",
    llm_prompt: str = "",
) -> MarkItDown:
    """Instancia el motor MarkItDown con soporte de código fuente y sesión HTTP optimizada para la web."""
    session = requests.Session()
    session.headers.update(
        {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
            ),
            "Accept": "text/markdown, text/html, application/xhtml+xml, application/xml;q=0.9, */*;q=0.8",
            "Accept-Language": "es-ES,es;q=0.9,en;q=0.8",
        }
    )

    kwargs = {
        "enable_plugins": enable_plugins,
        "requests_session": session,
    }

    if enable_plugins and openai_api_key.strip():
        try:
            from openai import OpenAI

            client = OpenAI(api_key=openai_api_key.strip())
            kwargs["llm_client"] = client
            kwargs["llm_model"] = llm_model
            if llm_prompt.strip():
                kwargs["llm_prompt"] = llm_prompt.strip()
        except ImportError:
            st.sidebar.warning(
                "Aviso: La librería 'openai' no está instalada. El OCR con LLM estará deshabilitado."
            )

    md = MarkItDown(**kwargs)
    # Registrar el convertidor de código fuente con prioridad más alta que PlainText
    md.register_converter(SourceCodeConverter(), priority=-0.5)
    return md


# ------------------------------
# Barra Lateral (Configuración)
# ------------------------------
with st.sidebar:
    st.image(
        "https://api.iconify.design/lucide:file-text.svg?color=%232563eb",
        width=50,
    )
    st.markdown("### Configuración del Motor")

    enable_plugins = st.toggle(
        "Habilitar Plugins / OCR",
        value=False,
        help="Permite utilizar convertidores extendidos como OCR basado en modelos de visión.",
    )

    openai_key = ""
    llm_model = "gpt-4o"
    llm_prompt = ""

    if enable_plugins:
        st.markdown("#### Ajustes de Visión / OCR")
        openai_key = st.text_input(
            "OpenAI API Key (o compatible)",
            type="password",
            value=os.environ.get("OPENAI_API_KEY", ""),
            help="Clave para utilizar OCR de páginas escaneadas o imágenes embebidas.",
        )
        llm_model = st.selectbox(
            "Modelo de Visión",
            ["gpt-4o", "gpt-4o-mini", "chatgpt-4o-latest"],
            index=0,
        )
        llm_prompt = st.text_area(
            "Prompt de OCR (opcional)",
            value="Extrae todo el texto manteniendo tablas, listas y formato original.",
            height=80,
        )

    st.markdown("---")
    st.markdown("#### Guardado en Disco Local")
    auto_save = st.checkbox(
        "Guardar automáticamente en disco",
        value=True,
        help="Guarda una copia de cada archivo convertido directamente en una carpeta de tu equipo.",
    )
    output_dir_input = st.text_input(
        "Carpeta de destino",
        value=DEFAULT_OUTPUT_DIR,
        disabled=not auto_save,
        help="Ruta donde se escribirán los archivos .md generados.",
    )

    st.markdown("---")
    st.markdown("#### Formatos Soportados")
    st.markdown(
        """
        <div class="format-cat">Documentos Ofimáticos</div>
        <span class="format-pill">PDF</span>
        <span class="format-pill">DOCX</span>
        <span class="format-pill">XLSX</span>
        <span class="format-pill">XLS</span>
        <span class="format-pill">PPTX</span>
        <span class="format-pill">EPUB</span>
        <span class="format-pill">RTF</span>

        <div class="format-cat">Código y Desarrollo</div>
        <span class="format-pill">Python</span>
        <span class="format-pill">Java</span>
        <span class="format-pill">C / C++</span>
        <span class="format-pill">C#</span>
        <span class="format-pill">Rust</span>
        <span class="format-pill">Go</span>
        <span class="format-pill">R</span>
        <span class="format-pill">JS / TS</span>
        <span class="format-pill">Shell/Bash</span>
        <span class="format-pill">SQL</span>
        <span class="format-pill">PHP</span>
        <span class="format-pill">Ruby</span>
        <span class="format-pill">Kotlin</span>
        <span class="format-pill">Swift</span>
        <span class="format-pill">Dart</span>
        <span class="format-pill">HTML/CSS</span>

        <div class="format-cat">Configuración y DevOps</div>
        <span class="format-pill">YAML</span>
        <span class="format-pill">JSON</span>
        <span class="format-pill">TOML</span>
        <span class="format-pill">XML</span>
        <span class="format-pill">Dockerfile</span>
        <span class="format-pill">Makefile</span>
        <span class="format-pill">.env</span>

        <div class="format-cat">Datos y Texto Plano</div>
        <span class="format-pill">CSV</span>
        <span class="format-pill">TSV</span>
        <span class="format-pill">TXT</span>
        <span class="format-pill">LOG</span>
        <span class="format-pill">MD</span>

        <div class="format-cat">Multimedia y Metadatos</div>
        <span class="format-pill">JPG/JPEG</span>
        <span class="format-pill">PNG</span>
        <span class="format-pill">MP3</span>
        <span class="format-pill">WAV</span>
        <span class="format-pill">M4A</span>

        <div class="format-cat">Web y Proyectos</div>
        <span class="format-pill">URL / Web</span>
        <span class="format-pill">Wikipedia</span>
        <span class="format-pill">ZIP</span>
        <span class="format-pill">Repositorio</span>
        """,
        unsafe_allow_html=True,
    )

    with st.expander("Catálogo Técnico Completo", expanded=False):
        st.markdown(
            """
            | Categoría | Tipos y Extensiones | Salida Markdown Generada |
            | :--- | :--- | :--- |
            | **PDF** | `.pdf` | Texto estructurado y tablas alineadas |
            | **Microsoft Office** | `.docx`, `.pptx` | Títulos, listas, párrafos y notas |
            | **Hojas de Cálculo** | `.xlsx`, `.xls` | Tablas nativas en Markdown con formato tabular |
            | **Libros y Enriquecido** | `.epub`, `.rtf` | Capítulos limpios y secciones formateadas |
            | **Código Fuente** | `.py`, `.java`, `.r`, `.sh`, `.js`, `.ts`, `.c`, `.cpp`, `.cs`, `.rs`, `.go`, `.sql`, etc. | Bloques de código con resaltado sintáctico de lenguaje |
            | **DevOps y Build** | `Dockerfile`, `Makefile`, `CMakeLists.txt`, `Jenkinsfile`, `.yml`, `.json`, `.toml` | Archivos de despliegue, pipelines y configuración |
            | **Datos Tabulares** | `.csv`, `.tsv`, `.json`, `.xml` | Datos estructurados limpios para prompts de LLM |
            | **Contenido Web** | URLs `http://`, `https://`, Wikipedia | Extracción de contenido principal sin cabeceras ni anuncios |
            | **Multimedia** | `.jpg`, `.png`, `.mp3`, `.wav` | Metadatos EXIF / transcripción y descripción OCR |
            | **Proyectos de Software** | Carpetas locales, `.zip` | Estructura espejo `sources/`, `TREE.md` y `CONSOLIDATED.md` |
            """
        )
    st.markdown("---")
    st.caption("Thoth Scann v0.1 | Motor MarkItDown")


# ------------------------------
# Cabecera Principal
# ------------------------------
st.markdown('<div class="main-title">Thoth Scann</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="subtitle">Digitalización y conversión inteligente de documentos y código a Markdown optimizado para LLMs y RAG.</div>',
    unsafe_allow_html=True,
)

tab_single, tab_batch, tab_project, tab_url = st.tabs(
    [
        "Documento Individual",
        "Procesamiento por Lotes",
        "Repositorio / Proyecto",
        "Conversión Web / URL",
    ]
)

# ==========================================
# PESTAÑA 1: DOCUMENTO INDIVIDUAL
# ==========================================
with tab_single:
    col_upload, col_action = st.columns([3, 1])

    with col_upload:
        uploaded_file = st.file_uploader(
            "Selecciona o arrastra cualquier archivo aquí (PDF, DOCX, ZIP o código .java, .py, .r, .sh, .yml, etc.)",
            type=None,
            help="Admite documentos, imágenes, audio, archivos comprimidos .zip y cualquier archivo de código fuente.",
            key="single_uploader",
        )

    if uploaded_file is not None:
        file_bytes = uploaded_file.getvalue()
        file_name = uploaded_file.name
        file_size = len(file_bytes)
        file_ext = Path(file_name).suffix.lower()
        base_name = Path(file_name).stem

        with col_action:
            st.markdown("#### Información")
            st.write(f"**Archivo:** `{file_name}`")
            st.write(f"**Tamaño:** {format_bytes(file_size)}")
            st.write(f"**Extensión:** `{file_ext}`")
            btn_convert = st.button(
                "Convertir a Markdown", type="primary", use_container_width=True
            )

        # Configuración opcional de particionado (Solo para Documento Individual)
        with st.expander(
            "Opciones de División del Documento (Para libros y textos extensos)",
            expanded=False,
        ):
            enable_split = st.checkbox(
                "Dividir documento en partes (Para libros o documentos extensos)",
                value=False,
                help="Divide el documento en múltiples fragmentos Markdown estructurados, generando automáticamente un índice maestro e inyectando metadatos para que la IA reconozca la continuidad de la obra.",
                key="single_enable_split",
            )
            if enable_split:
                col_split1, col_split2 = st.columns(2)
                with col_split1:
                    split_mode_choice = st.selectbox(
                        "Criterio de división",
                        options=[
                            "Por límite de tokens (Recomendado para LLMs)",
                            "Por número fijo de partes",
                            "Por capítulos / encabezados Markdown (# o ##)",
                        ],
                        index=0,
                        key="single_split_mode",
                    )
                with col_split2:
                    if "tokens" in split_mode_choice.lower():
                        split_tokens = st.slider(
                            "Tokens máximos por parte",
                            min_value=5000,
                            max_value=100000,
                            value=25000,
                            step=5000,
                            help="Aproximación estándar: 1 token ≈ 4 caracteres. 25,000 tokens ≈ 100,000 caracteres.",
                            key="single_split_tokens",
                        )
                        split_mode = "tokens"
                        split_parts_num = 3
                        split_heading_lvl = 1
                    elif "fijo" in split_mode_choice.lower():
                        split_parts_num = st.slider(
                            "Número de partes",
                            min_value=2,
                            max_value=20,
                            value=4,
                            step=1,
                            help="Divide el documento en N fragmentos de tamaño equilibrado respetando límites de párrafos.",
                            key="single_split_parts",
                        )
                        split_mode = "parts"
                        split_tokens = 25000
                        split_heading_lvl = 1
                    else:
                        split_heading_choice = st.selectbox(
                            "Nivel de encabezado para división",
                            options=[
                                "Nivel 1 (# Título / Capítulo)",
                                "Nivel 2 (## Subtítulo / Sección)",
                            ],
                            index=1,
                            key="single_split_heading",
                        )
                        split_heading_lvl = (
                            1 if "Nivel 1" in split_heading_choice else 2
                        )
                        split_mode = "headings"
                        split_tokens = 25000
                        split_parts_num = 3

                inject_ai_context = st.checkbox(
                    "Inyectar metadatos de contexto para IA (YAML Frontmatter + Banner de Continuidad + Índice Maestro)",
                    value=True,
                    help="Permite a los modelos de lenguaje (LLM/IAG) identificar que cada fragmento pertenece al mismo documento, reconociendo la parte actual, enlaces cruzados y el mapa temático global.",
                    key="single_inject_context",
                )
            else:
                split_mode = "tokens"
                split_tokens = 25000
                split_parts_num = 3
                split_heading_lvl = 1
                inject_ai_context = True

        # Ejecución de la conversión
        if btn_convert or "last_converted_single" in st.session_state:
            # Si el usuario hace click o ya convirtió este archivo
            if btn_convert or st.session_state.get("last_filename") == file_name:
                with st.spinner("Procesando y convirtiendo documento..."):
                    start_time = time.time()
                    try:
                        md = get_markitdown_instance(
                            enable_plugins=enable_plugins,
                            openai_api_key=openai_key,
                            llm_model=llm_model,
                            llm_prompt=llm_prompt,
                        )

                        stream = io.BytesIO(file_bytes)
                        stream_info = StreamInfo(
                            filename=file_name,
                            extension=file_ext,
                        )

                        result = md.convert_stream(stream, stream_info=stream_info)
                        elapsed = time.time() - start_time

                        markdown_text = result.markdown
                        st.session_state["last_converted_single"] = markdown_text
                        st.session_state["last_filename"] = file_name
                        st.session_state["last_elapsed"] = elapsed

                    except Exception as e:
                        st.error(f"Error al convertir el archivo: {str(e)}")
                        st.stop()

            # Recuperar resultado almacenado
            markdown_output = st.session_state.get("last_converted_single", "")
            elapsed = st.session_state.get("last_elapsed", 0.0)

            if enable_split and markdown_output:
                # Procesar particionado del documento
                split_opts = SplitOptions(
                    mode=split_mode,
                    target_tokens=split_tokens,
                    num_parts=split_parts_num,
                    heading_level=split_heading_lvl,
                    inject_ai_context=inject_ai_context,
                    base_name=base_name,
                    original_filename=file_name,
                )
                split_result = DocumentSplitter.split_document(markdown_output, split_opts)

                st.success(
                    f"Conversión y particionado completados en {elapsed:.2f} segundos. "
                    f"Se generaron {len(split_result.parts)} partes con índice maestro."
                )

                # Métricas del particionado
                sm1, sm2, sm3, sm4 = st.columns(4)
                sm1.metric("Partes Generadas", f"{len(split_result.parts)}")
                sm2.metric("Tokens Totales (LLM)", f"~{split_result.total_tokens:,}")
                avg_tokens = (
                    int(split_result.total_tokens / len(split_result.parts))
                    if split_result.parts
                    else 0
                )
                sm3.metric("Promedio por Parte", f"~{avg_tokens:,} tokens")
                with sm4:
                    st.download_button(
                        label="Descargar Todas las Partes (.zip)",
                        data=split_result.get_zip_bytes(),
                        file_name=f"{base_name}_partes.zip",
                        mime="application/zip",
                        type="primary",
                        use_container_width=True,
                    )

                # Guardado automático en disco si está habilitado
                if auto_save and output_dir_input.strip():
                    try:
                        out_dir = Path(output_dir_input.strip())
                        saved_dir = split_result.save_to_disk(out_dir)
                        st.info(f"**Partes e índice guardados en disco:** `{saved_dir}`")
                    except Exception as save_err:
                        st.warning(f"Aviso: No se pudo guardar en disco: {save_err}")

                st.markdown("---")
                st.info(
                    "**Preservación de Contexto para IA:** Cada parte incluye encabezados YAML Frontmatter estandarizados, "
                    "banner de navegación y pie de página de continuidad. El archivo índice (`_INDEX.md`) resume todo el documento "
                    "para permitir a la IA o sistemas RAG saber de inmediato que se trata del mismo documento dividido."
                )

                # Desglose de partes y descarga individual
                st.markdown("##### Catálogo de Partes Generadas")
                col_idx1, col_idx2 = st.columns([3, 1])
                with col_idx1:
                    st.write(f"Manifiesto principal: **`{split_result.index_filename}`**")
                with col_idx2:
                    st.download_button(
                        label="Descargar Índice Maestro (.md)",
                        data=split_result.index_markdown,
                        file_name=split_result.index_filename,
                        mime="text/markdown",
                        use_container_width=True,
                    )

                # Mostrar partes en acordeones limpios con botón de descarga individual
                for part in split_result.parts:
                    with st.expander(
                        f"Parte {part.part_number} de {part.total_parts}: {part.filename} (~{part.token_estimate:,} tokens)",
                        expanded=False,
                    ):
                        p_col1, p_col2 = st.columns([3, 1])
                        with p_col1:
                            st.caption(
                                f"Caracteres: {part.char_count:,} | Palabras: {part.word_count:,} | Sección: {part.first_heading}"
                            )
                        with p_col2:
                            st.download_button(
                                label=f"Descargar Parte {part.part_number}",
                                data=part.content,
                                file_name=part.filename,
                                mime="text/markdown",
                                key=f"dl_part_{part.part_number}",
                                use_container_width=True,
                            )
                        sample_limit = 2000
                        if len(part.content) > sample_limit:
                            st.code(
                                part.content[:sample_limit]
                                + "\n\n[... resto del contenido omitido en vista previa ...]",
                                language="markdown",
                            )
                        else:
                            st.code(part.content, language="markdown")

                with st.expander(
                    "Inspeccionar Índice Maestro completo (INDEX.md)", expanded=False
                ):
                    st.code(split_result.index_markdown, language="markdown")

            else:
                # Flujo estándar sin división
                char_count = len(markdown_output)
                word_count = len(markdown_output.split())
                token_estimate = int(char_count / 4)

                st.success(f"Conversión completada en {elapsed:.2f} segundos.")

                m_col1, m_col2, m_col3, m_col4 = st.columns(4)
                m_col1.metric("Caracteres", f"{char_count:,}")
                m_col2.metric("Palabras", f"{word_count:,}")
                m_col3.metric("Tokens aprox. (LLM)", f"~{token_estimate:,}")
                with m_col4:
                    st.download_button(
                        label="Descargar Markdown (.md)",
                        data=markdown_output,
                        file_name=f"{base_name}.md",
                        mime="text/markdown",
                        use_container_width=True,
                    )

                # Guardado automático en disco
                if auto_save and output_dir_input.strip():
                    try:
                        out_dir = Path(output_dir_input.strip())
                        out_dir.mkdir(parents=True, exist_ok=True)
                        target_file = out_dir / f"{base_name}.md"
                        target_file.write_text(markdown_output, encoding="utf-8")
                        st.info(f"**Archivo guardado en disco:** `{target_file}`")
                    except Exception as save_err:
                        st.warning(f"Aviso: No se pudo guardar en disco: {save_err}")

                st.markdown("---")
                st.info(
                    "Extracción completada y lista para su uso. La vista previa automática en pantalla está desactivada "
                    "para maximizar la velocidad de procesamiento y evitar consumo innecesario de recursos en documentos grandes."
                )

                with st.expander(
                    "Inspeccionar muestra del texto extraído (opcional)", expanded=False
                ):
                    preview_limit = 4000
                    if len(markdown_output) > preview_limit:
                        st.caption(
                            f"Mostrando los primeros {preview_limit:,} caracteres de {char_count:,} totales:"
                        )
                        st.code(
                            markdown_output[:preview_limit], language="markdown"
                        )
                    else:
                        st.code(markdown_output, language="markdown")


# ==========================================
# PESTAÑA 2: PROCESAMIENTO POR LOTES
# ==========================================
with tab_batch:
    st.markdown("#### Conversión de Múltiples Archivos en Lote")
    st.write(
        "Arrastra varios documentos simultáneamente. Podrás procesarlos todos y descargar un archivo ZIP con los Markdowns generados."
    )

    batch_files = st.file_uploader(
        "Selecciona o arrastra varios archivos (Documentos o archivos de código)",
        type=None,
        accept_multiple_files=True,
        help="Admite documentos, imágenes, audio, archivos comprimidos .zip y cualquier archivo de código fuente (.java, .py, .r, .sh, .yml, etc.).",
        key="batch_uploader",
    )

    if batch_files:
        st.write(f"Archivos seleccionados: **{len(batch_files)}**")
        btn_batch_convert = st.button(
            "Procesar todos los archivos", type="primary"
        )

        if btn_batch_convert:
            md = get_markitdown_instance(
                enable_plugins=enable_plugins,
                openai_api_key=openai_key,
                llm_model=llm_model,
                llm_prompt=llm_prompt,
            )

            progress_bar = st.progress(0)
            status_text = st.empty()

            results_dict = {}
            total = len(batch_files)

            start_batch = time.time()
            for idx, file in enumerate(batch_files):
                status_text.text(f"Procesando ({idx + 1}/{total}): {file.name}...")
                file_bytes = file.getvalue()
                file_ext = Path(file.name).suffix.lower()

                try:
                    stream = io.BytesIO(file_bytes)
                    stream_info = StreamInfo(filename=file.name, extension=file_ext)
                    res = md.convert_stream(stream, stream_info=stream_info)
                    results_dict[file.name] = {
                        "status": "success",
                        "markdown": res.markdown,
                        "words": len(res.markdown.split()),
                    }
                except Exception as e:
                    results_dict[file.name] = {
                        "status": "error",
                        "error": str(e),
                        "words": 0,
                    }

                progress_bar.progress((idx + 1) / total)

            batch_elapsed = time.time() - start_batch
            status_text.text(
                f"Lote completado en {batch_elapsed:.2f}s ({total} archivos)."
            )

            # Generar ZIP con los resultados exitosos
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
                for orig_name, info in results_dict.items():
                    if info["status"] == "success":
                        md_filename = f"{Path(orig_name).stem}.md"
                        zip_file.writestr(md_filename, info["markdown"])

            zip_buffer.seek(0)

            # Botón de descarga del ZIP
            st.download_button(
                label="Descargar todos los Markdown (.zip)",
                data=zip_buffer,
                file_name="thoth_markdown_batch.zip",
                mime="application/zip",
                type="primary",
            )

            # Guardado automático en disco si está activado
            if auto_save and output_dir_input.strip():
                try:
                    out_dir = Path(output_dir_input.strip())
                    out_dir.mkdir(parents=True, exist_ok=True)
                    saved_count = 0
                    for orig_name, info in results_dict.items():
                        if info["status"] == "success":
                            target_file = out_dir / f"{Path(orig_name).stem}.md"
                            target_file.write_text(info["markdown"], encoding="utf-8")
                            saved_count += 1
                    if saved_count > 0:
                        st.info(
                            f"**{saved_count} archivos guardados automáticamente en:** `{out_dir}`"
                        )
                except Exception as save_err:
                    st.warning(
                        f"Aviso: No se pudieron guardar los archivos en disco: {save_err}"
                    )

            # Tabla resumen de resultados
            summary_data = []
            for name, info in results_dict.items():
                if info["status"] == "success":
                    summary_data.append(
                        {
                            "Archivo": name,
                            "Estado": "Correcto",
                            "Palabras": f"{info['words']:,}",
                            "Detalle": "OK",
                        }
                    )
                else:
                    summary_data.append(
                        {
                            "Archivo": name,
                            "Estado": "Fallido",
                            "Palabras": "0",
                            "Detalle": info.get("error", "Error desconocido"),
                        }
                    )

            st.dataframe(summary_data, use_container_width=True)

# ==========================================
# PESTAÑA 3: REPOSITORIO / PROYECTO COMPLETO
# ==========================================
with tab_project:
    st.markdown("#### Extracción y Documentación de Proyectos Completos")
    st.write(
        "Escanea un repositorio o carpeta de software completo. Genera el mapa jerárquico (**TREE.md**), "
        "la estructura espejo de archivos individuales para RAG/agentes (**sources/**) "
        "y un documento consolidado todo-en-uno (**CONSOLIDATED.md**) para LLMs de contexto largo."
    )

    proj_input_mode = st.radio(
        "Método de entrada",
        [
            "Carpeta Local en Disco (Rápido, sin subida)",
            "Archivo ZIP del Proyecto",
        ],
        horizontal=True,
    )

    proj_folder_path = ""
    proj_zip_file = None
    custom_proj_name = ""

    if "Carpeta Local" in proj_input_mode:
        c_p1, c_p2 = st.columns([3, 1])
        with c_p1:
            proj_folder_path = st.text_input(
                "Ruta absoluta de la carpeta del proyecto en tu equipo",
                value=str(BASE_DIR / "markitdown-main"),
                help="Ruta directa de la carpeta en disco. No requiere subida por navegador.",
            )
        with c_p2:
            custom_proj_name = st.text_input(
                "Nombre del proyecto (opcional)",
                value="",
                placeholder="Autodetectar de la carpeta",
            )
    else:
        c_z1, c_z2 = st.columns([3, 1])
        with c_z1:
            proj_zip_file = st.file_uploader(
                "Sube el archivo ZIP con el proyecto de software",
                type=["zip"],
                key="project_zip_uploader",
            )
        with c_z2:
            custom_proj_name = st.text_input(
                "Nombre del proyecto (opcional)",
                value="",
                placeholder="Autodetectar del ZIP",
            )

    st.markdown("##### Opciones de Generación")
    opt_c1, opt_c2, opt_c3 = st.columns(3)
    with opt_c1:
        gen_tree = st.checkbox("Generar TREE.md (Mapa de contexto)", value=True)
    with opt_c2:
        gen_separate = st.checkbox(
            "Estructura Espejo (sources/ para RAG)", value=True
        )
    with opt_c3:
        gen_consolidated = st.checkbox(
            "Archivo CONSOLIDATED.md (Para chats LLM)", value=True
        )

    btn_extract_project = st.button(
        "Extraer y Documentar Proyecto", type="primary"
    )

    if btn_extract_project:
        out_base = Path(
            output_dir_input.strip()
            if auto_save and output_dir_input.strip()
            else DEFAULT_OUTPUT_DIR
        )
        opts = ExtractionOptions(
            generate_tree=gen_tree,
            generate_separate_files=gen_separate,
            generate_consolidated=gen_consolidated,
        )

        with st.spinner("Escaneando repositorio y estructurando código..."):
            start_proj = time.time()
            try:
                res_proj = None
                if "Carpeta Local" in proj_input_mode:
                    if (
                        not proj_folder_path.strip()
                        or not Path(proj_folder_path.strip()).is_dir()
                    ):
                        st.error(
                            f"Error: La ruta especificada no es una carpeta válida: `{proj_folder_path}`"
                        )
                        st.stop()
                    res_proj = extract_directory(
                        source_dir=proj_folder_path.strip(),
                        output_base_dir=out_base,
                        options=opts,
                    )
                else:
                    if proj_zip_file is None:
                        st.error(
                            "Error: Por favor selecciona un archivo ZIP para procesar."
                        )
                        st.stop()
                    p_name = (
                        custom_proj_name.strip()
                        or Path(proj_zip_file.name).stem
                    )
                    res_proj = extract_zip(
                        zip_source=io.BytesIO(proj_zip_file.getvalue()),
                        output_base_dir=out_base,
                        project_name=p_name,
                        options=opts,
                    )

                elapsed_proj = time.time() - start_proj
                st.session_state["last_project_result"] = res_proj
                st.session_state["last_project_elapsed"] = elapsed_proj

            except Exception as e:
                st.error(
                    f"Error durante la extracción del proyecto: {str(e)}"
                )
                st.stop()

    if "last_project_result" in st.session_state:
        res_proj = st.session_state["last_project_result"]
        elapsed_proj = st.session_state.get("last_project_elapsed", 0.0)

        st.success(
            f"Proyecto `{res_proj.project_name}` documentado con éxito en {elapsed_proj:.2f}s."
        )
        st.info(f"**Directorio de salida en disco:** `{res_proj.output_dir}`")

        # Métricas principales
        pm1, pm2, pm3, pm4 = st.columns(4)
        pm1.metric("Archivos Procesados", f"{res_proj.total_files:,}")
        pm2.metric("Líneas de Código", f"{res_proj.total_lines:,}")
        pm3.metric("Tokens aprox. (LLM)", f"~{res_proj.token_estimate:,}")
        top_lang = (
            max(res_proj.language_stats.items(), key=lambda x: x[1]["lines"])[
                0
            ]
            if res_proj.language_stats
            else "N/A"
        )
        pm4.metric("Lenguaje Principal", str(top_lang).upper())

        # Botones de descarga
        d_col1, d_col2 = st.columns(2)
        with d_col1:
            if (
                res_proj.consolidated_path
                and res_proj.consolidated_path.exists()
            ):
                st.download_button(
                    label="Descargar CONSOLIDATED.md (Consolidado)",
                    data=res_proj.consolidated_path.read_text(encoding="utf-8"),
                    file_name=f"{res_proj.project_name}_CONSOLIDATED.md",
                    mime="text/markdown",
                    use_container_width=True,
                )
        with d_col2:
            run_zip_buf = io.BytesIO()
            with zipfile.ZipFile(
                run_zip_buf, "w", zipfile.ZIP_DEFLATED
            ) as rz:
                for r_root, _, r_files in os.walk(res_proj.output_dir):
                    for rf in r_files:
                        rf_abs = Path(r_root) / rf
                        rf_rel = rf_abs.relative_to(res_proj.output_dir)
                        rz.write(rf_abs, arcname=str(rf_rel))
            run_zip_buf.seek(0)
            st.download_button(
                label="Descargar Paquete Completo (.zip con Tree y Sources)",
                data=run_zip_buf,
                file_name=f"{res_proj.project_name}_documentado.zip",
                mime="application/zip",
                use_container_width=True,
            )

        st.markdown("---")

        # Pestañas de inspección visual
        pt1, pt2, pt3 = st.tabs(
            [
                "Mapa de Directorios (TREE.md)",
                "Vista Consolidada",
                "Distribución de Lenguajes",
            ]
        )

        with pt1:
            if res_proj.tree_path and res_proj.tree_path.exists():
                st.markdown(res_proj.tree_path.read_text(encoding="utf-8"))
            else:
                st.code(res_proj.tree_content)

        with pt2:
            if (
                res_proj.consolidated_path
                and res_proj.consolidated_path.exists()
            ):
                st.success(f"Archivo consolidado generado en: `{res_proj.consolidated_path}`")
                st.info(
                    "El archivo CONSOLIDATED.md reúne todo el código del repositorio estructurado y delimitado para LLMs. "
                    "Para máxima velocidad y evitar sobrecarga del navegador, utiliza los botones de descarga superiores."
                )
                with st.expander("Inspeccionar muestra de CONSOLIDATED.md (primeras 100 líneas)", expanded=False):
                    try:
                        raw_lines = res_proj.consolidated_path.read_text(
                            encoding="utf-8", errors="replace"
                        ).splitlines()
                        sample_preview = "\n".join(raw_lines[:100])
                        st.code(sample_preview, language="markdown")
                        if len(raw_lines) > 100:
                            st.caption(f"Mostrando 100 líneas de {len(raw_lines):,} líneas totales.")
                    except Exception as err:
                        st.warning(f"No fue posible leer la muestra: {err}")
            else:
                st.info(
                    "La opción de archivo consolidado no fue seleccionada."
                )

        with pt3:
            lang_table_data = []
            for l_name, l_data in sorted(
                res_proj.language_stats.items(),
                key=lambda x: x[1]["lines"],
                reverse=True,
            ):
                l_pct = (
                    (l_data["lines"] / res_proj.total_lines * 100)
                    if res_proj.total_lines > 0
                    else 0
                )
                lang_table_data.append(
                    {
                        "Lenguaje": l_name.upper(),
                        "Archivos": l_data["files"],
                        "Líneas": f"{l_data['lines']:,}",
                        "Porcentaje": f"{l_pct:.1f}%",
                    }
                )
            st.dataframe(lang_table_data, use_container_width=True)

# ==========================================
# PESTAÑA 4: CONVERSIÓN DESDE URL
# ==========================================
with tab_url:
    st.markdown("#### Convertir Contenido Web a Markdown")
    st.write(
        "Extrae y limpia artículos, documentación técnica, entradas de blog, páginas Wikipedia "
        "o recursos web directamente a Markdown optimizado para LLMs."
    )

    url_col1, url_col2 = st.columns([3, 1])
    with url_col1:
        url_input = st.text_input(
            "URL de origen",
            placeholder="https://es.wikipedia.org/wiki/Escriba_en_el_Antiguo_Egipto",
            help="Introduce la dirección completa o el dominio. Se admite HTTP, HTTPS y enlaces directos.",
        )
    with url_col2:
        st.write("")
        st.write("")
        btn_url_convert = st.button("Convertir URL", type="primary", use_container_width=True)

    st.caption(
        "Ejemplos: `https://es.wikipedia.org/wiki/Inteligencia_artificial` | "
        "`https://httpbin.org/html`"
    )

    if btn_url_convert and url_input.strip():
        raw_url = url_input.strip()
        # Normalizar esquema si se omitió http(s)://
        if not re.match(r"^[a-zA-Z]+://", raw_url):
            raw_url = "https://" + raw_url

        with st.spinner(f"Descargando y convirtiendo {raw_url}..."):
            start_url = time.time()
            try:
                md = get_markitdown_instance(enable_plugins=enable_plugins)
                result_url = md.convert(raw_url)
                elapsed_url = time.time() - start_url

                web_markdown = result_url.markdown or ""
                web_title = result_url.title or "Contenido Web"
                char_count = len(web_markdown)
                word_count = len(web_markdown.split())
                token_estimate = int(char_count / 4)

                # Generar nombre de archivo limpio basado en el dominio y ruta
                parsed = urlparse(raw_url)
                netloc_clean = re.sub(r"[^\w\-.]", "_", parsed.netloc.replace("www.", ""))
                path_clean = re.sub(r"[^\w\-.]", "_", parsed.path.strip("/").replace("/", "_"))
                slug_base = f"{netloc_clean}_{path_clean}".strip("_") if path_clean else (netloc_clean or "web_content")
                slug_file = (slug_base[:60] or "web_content") + ".md"

                st.success(f"URL convertida exitosamente en {elapsed_url:.2f} segundos.")
                if result_url.title:
                    st.markdown(f"**Título:** `{result_url.title}`")

                # Métricas
                m1, m2, m3, m4 = st.columns(4)
                m1.metric("Caracteres", f"{char_count:,}")
                m2.metric("Palabras", f"{word_count:,}")
                m3.metric("Tokens aprox. (LLM)", f"~{token_estimate:,}")
                with m4:
                    st.download_button(
                        label="Descargar Markdown (.md)",
                        data=web_markdown,
                        file_name=slug_file,
                        mime="text/markdown",
                        use_container_width=True,
                    )

                # Guardado automático en disco local
                if auto_save and output_dir_input.strip():
                    try:
                        out_dir = Path(output_dir_input.strip())
                        out_dir.mkdir(parents=True, exist_ok=True)
                        target_file = out_dir / slug_file
                        target_file.write_text(web_markdown, encoding="utf-8")
                        st.info(f"**Archivo guardado en disco:** `{target_file}`")
                    except Exception as save_err:
                        st.warning(f"Aviso: No se pudo guardar en disco: {save_err}")

                st.markdown("---")
                st.info(
                    "Extracción web completada y lista para su uso. La vista previa automática completa se mantiene desactivada "
                    "para máxima fluidez. Puedes descargar el archivo directamente o revisar la muestra a continuación."
                )

                # Muestra opcional bajo demanda
                with st.expander("Inspeccionar muestra del texto web extraído (opcional)", expanded=False):
                    max_preview = 4000
                    if len(web_markdown) > max_preview:
                        st.caption(f"Mostrando primeros {max_preview:,} caracteres de {char_count:,} totales:")
                        st.code(web_markdown[:max_preview], language="markdown")
                    else:
                        st.code(web_markdown, language="markdown")

            except requests.exceptions.SSLError as ssl_err:
                st.error(f"Error de certificado SSL en el servidor remoto: {ssl_err}")
            except requests.exceptions.Timeout:
                st.error("Tiempo de espera agotado al conectar con el servidor web (el sitio no respondió a tiempo).")
            except requests.exceptions.ConnectionError:
                st.error("No se pudo establecer conexión con el dominio indicado. Verifica la URL y tu conexión a internet.")
            except requests.exceptions.HTTPError as http_err:
                st.error(f"El servidor web respondió con error HTTP: {http_err}")
            except Exception as e:
                st.error(f"Error al procesar la URL: {str(e)}")
