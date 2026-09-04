"""
Thoth Scann - Interfaz Gráfica de Usuario (UI)
Conversión inteligente de documentos a Markdown estructurado para LLMs y análisis documental.
Basado en el motor MarkItDown.
"""

import io
import os
import sys
import time
import zipfile
from pathlib import Path
import streamlit as st

# Importación del motor MarkItDown
try:
    from markitdown import MarkItDown, StreamInfo
except ImportError:
    st.error(
        "❌ El paquete 'markitdown' no está instalado en el entorno actual. "
        "Asegúrate de haber activado el entorno virtual (.venv)."
    )
    st.stop()


# Configuración de página
st.set_page_config(
    page_title="Thoth Scann | Conversor Documental",
    page_icon="📜",
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


def get_markitdown_instance(
    enable_plugins: bool = False,
    openai_api_key: str = "",
    llm_model: str = "gpt-4o",
    llm_prompt: str = "",
) -> MarkItDown:
    """Instancia el motor MarkItDown con la configuración seleccionada."""
    kwargs = {"enable_plugins": enable_plugins}

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
                "⚠️ La librería 'openai' no está instalada. El OCR con LLM estará deshabilitado."
            )

    return MarkItDown(**kwargs)


# ------------------------------
# Barra Lateral (Configuración)
# ------------------------------
with st.sidebar:
    st.image(
        "https://api.iconify.design/lucide:file-text.svg?color=%232563eb",
        width=50,
    )
    st.markdown("### ⚙️ Configuración del Motor")

    enable_plugins = st.toggle(
        "Habilitar Plugins / OCR",
        value=False,
        help="Permite utilizar convertidores extendidos como OCR basado en modelos de visión.",
    )

    openai_key = ""
    llm_model = "gpt-4o"
    llm_prompt = ""

    if enable_plugins:
        st.markdown("#### 👁️ Ajustes de Visión / OCR")
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
    st.markdown("#### 📁 Guardado en Disco Local")
    auto_save = st.checkbox(
        "Guardar automáticamente en disco",
        value=True,
        help="Guarda una copia de cada archivo convertido directamente en una carpeta de tu equipo.",
    )
    output_dir_input = st.text_input(
        "Carpeta de destino",
        value="/home/massive-usr/Documentos/desarrollo/thoth_scann/output",
        disabled=not auto_save,
        help="Ruta donde se escribirán los archivos .md generados.",
    )

    st.markdown("---")
    st.markdown("#### 📂 Formatos Soportados")
    st.markdown(
        """
        - **Documentos**: PDF, DOCX, PPTX, XLSX, XLS, EPUB
        - **Texto y Datos**: CSV, JSON, XML, HTML, TXT
        - **Multimedia**: JPG, PNG, MP3, WAV
        - **Contenedores**: Archivos ZIP (recursivo), Notebooks (.ipynb)
        - **Web**: Enlaces directos o URLs de Wikipedia
        """
    )
    st.markdown("---")
    st.caption("🚀 **Thoth Scann v0.1** | Motor MarkItDown")


# ------------------------------
# Cabecera Principal
# ------------------------------
st.markdown('<div class="main-title">📜 Thoth Scann</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="subtitle">Digitalización y conversión inteligente de documentos a Markdown optimizado para LLMs y RAG.</div>',
    unsafe_allow_html=True,
)

tab_single, tab_batch, tab_url = st.tabs(
    ["📄 Documento Individual", "📦 Procesamiento por Lotes", "🌐 Convertir desde URL"]
)

# ==========================================
# PESTAÑA 1: DOCUMENTO INDIVIDUAL
# ==========================================
with tab_single:
    col_upload, col_action = st.columns([3, 1])

    with col_upload:
        uploaded_file = st.file_uploader(
            "Selecciona o arrastra un archivo aquí",
            type=[
                "pdf",
                "docx",
                "xlsx",
                "xls",
                "pptx",
                "html",
                "csv",
                "json",
                "xml",
                "txt",
                "zip",
                "jpg",
                "jpeg",
                "png",
                "mp3",
                "wav",
                "ipynb",
                "epub",
            ],
            key="single_uploader",
        )

    if uploaded_file is not None:
        file_bytes = uploaded_file.getvalue()
        file_name = uploaded_file.name
        file_size = len(file_bytes)
        file_ext = Path(file_name).suffix.lower()

        with col_action:
            st.markdown("#### 📋 Información")
            st.write(f"**Archivo:** `{file_name}`")
            st.write(f"**Tamaño:** {format_bytes(file_size)}")
            st.write(f"**Extensión:** `{file_ext}`")
            btn_convert = st.button(
                "⚡ Convertir a Markdown", type="primary", use_container_width=True
            )

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
                        st.error(f"❌ Error al convertir el archivo: {str(e)}")
                        st.stop()

            # Recuperar resultado almacenado
            markdown_output = st.session_state.get("last_converted_single", "")
            elapsed = st.session_state.get("last_elapsed", 0.0)

            # Barra de métricas
            char_count = len(markdown_output)
            word_count = len(markdown_output.split())
            token_estimate = int(char_count / 4)

            st.success(f"✅ Conversión completada en {elapsed:.2f} segundos")

            m_col1, m_col2, m_col3, m_col4 = st.columns(4)
            m_col1.metric("Caracteres", f"{char_count:,}")
            m_col2.metric("Palabras", f"{word_count:,}")
            m_col3.metric("Tokens aprox. (LLM)", f"~{token_estimate:,}")
            with m_col4:
                base_name = Path(file_name).stem
                st.download_button(
                    label="📥 Descargar .md",
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
                    st.info(f"💾 **Copia guardada en disco:** `{target_file}`")
                except Exception as save_err:
                    st.warning(f"⚠️ No se pudo guardar en disco: {save_err}")

            st.markdown("---")

            # Vistas: Renderizada vs Código fuente
            subtab_preview, subtab_code = st.tabs(
                ["👁️ Vista Renderizada", "💻 Código Markdown (Raw)"]
            )

            with subtab_preview:
                if markdown_output.strip():
                    st.markdown(markdown_output)
                else:
                    st.info(
                        "El documento se procesó pero no produjo contenido de texto."
                    )

            with subtab_code:
                st.code(markdown_output, language="markdown", line_numbers=True)

# ==========================================
# PESTAÑA 2: PROCESAMIENTO POR LOTES
# ==========================================
with tab_batch:
    st.markdown("#### 📦 Conversión de Múltiples Archivos en Lote")
    st.write(
        "Arrastra varios documentos simultáneamente. Podrás procesarlos todos y descargar un archivo ZIP con los Markdowns generados."
    )

    batch_files = st.file_uploader(
        "Selecciona varios archivos",
        type=[
            "pdf",
            "docx",
            "xlsx",
            "xls",
            "pptx",
            "html",
            "csv",
            "json",
            "xml",
            "txt",
            "zip",
            "jpg",
            "jpeg",
            "png",
            "ipynb",
            "epub",
        ],
        accept_multiple_files=True,
        key="batch_uploader",
    )

    if batch_files:
        st.write(f"Archivos seleccionados: **{len(batch_files)}**")
        btn_batch_convert = st.button(
            "⚡ Procesar todos los archivos", type="primary"
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
                f"🎉 Lote completado en {batch_elapsed:.2f}s! ({total} archivos)"
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
                label="📥 Descargar todos los Markdown (.zip)",
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
                            f"💾 **{saved_count} archivos guardados automáticamente en:** `{out_dir}`"
                        )
                except Exception as save_err:
                    st.warning(
                        f"⚠️ No se pudieron guardar los archivos en disco: {save_err}"
                    )

            # Tabla resumen de resultados
            summary_data = []
            for name, info in results_dict.items():
                if info["status"] == "success":
                    summary_data.append(
                        {
                            "Archivo": name,
                            "Estado": "✅ Correcto",
                            "Palabras": f"{info['words']:,}",
                            "Detalle": "OK",
                        }
                    )
                else:
                    summary_data.append(
                        {
                            "Archivo": name,
                            "Estado": "❌ Falló",
                            "Palabras": "0",
                            "Detalle": info.get("error", "Error desconocido"),
                        }
                    )

            st.dataframe(summary_data, use_container_width=True)

# ==========================================
# PESTAÑA 3: CONVERSIÓN DESDE URL
# ==========================================
with tab_url:
    st.markdown("#### 🌐 Convertir Contenido Web a Markdown")
    st.write(
        "Pega la dirección URL de un artículo, página web, Wikipedia o recurso online:"
    )

    url_input = st.text_input(
        "URL de origen",
        placeholder="https://es.wikipedia.org/wiki/Escriba_en_el_Antiguo_Egipto",
    )
    btn_url_convert = st.button("⚡ Convertir URL", type="primary")

    if btn_url_convert and url_input.strip():
        with st.spinner(f"Descargando y convirtiendo {url_input}..."):
            start_url = time.time()
            try:
                md = get_markitdown_instance(enable_plugins=enable_plugins)
                result_url = md.convert(url_input.strip())
                elapsed_url = time.time() - start_url

                st.success(f"✅ URL convertida en {elapsed_url:.2f} segundos")

                c1, c2 = st.columns([3, 1])
                with c2:
                    st.download_button(
                        label="📥 Descargar .md",
                        data=result_url.markdown,
                        file_name="web_content.md",
                        mime="text/markdown",
                        use_container_width=True,
                    )

                # Guardado automático en disco
                if auto_save and output_dir_input.strip():
                    try:
                        out_dir = Path(output_dir_input.strip())
                        out_dir.mkdir(parents=True, exist_ok=True)
                        from urllib.parse import urlparse
                        slug = (
                            urlparse(url_input.strip())
                            .path.strip("/")
                            .replace("/", "_")
                            or "web_content"
                        )
                        target_file = out_dir / f"{slug}.md"
                        target_file.write_text(result_url.markdown, encoding="utf-8")
                        st.info(f"💾 **Copia guardada en disco:** `{target_file}`")
                    except Exception as save_err:
                        st.warning(f"⚠️ No se pudo guardar en disco: {save_err}")

                u_tab1, u_tab2 = st.tabs(
                    ["👁️ Vista Renderizada", "💻 Código Markdown (Raw)"]
                )
                with u_tab1:
                    st.markdown(result_url.markdown)
                with u_tab2:
                    st.code(result_url.markdown, language="markdown")

            except Exception as e:
                st.error(f"❌ Error al procesar la URL: {str(e)}")
