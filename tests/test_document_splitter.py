import io
from pathlib import Path
import sys
import tempfile
import zipfile

# Asegurar que el directorio raíz esté en sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from thoth_extractor.document_splitter import (
    DocumentSplitter,
    SplitOptions,
    DocumentPart,
    SplitResult,
)


def get_sample_markdown_book() -> str:

    return """# Manual de Arquitectura de Software

Este es un libro de referencia para ingeniería de software moderna.

## Capítulo 1: Fundamentos y Principios

Los principios SOLID permiten estructurar código mantenible y desacoplado a largo plazo.
La arquitectura limpia separa las reglas de negocio de los detalles tecnológicos externos.

```python
def calculate_metrics(data: list) -> dict:
    # Bloque de código que no debe ser fracturado
    total = sum(data)
    return {"total": total, "average": total / len(data)}
```

El principio de responsabilidad única asegura que cada clase tenga un único motivo de cambio.

## Capítulo 2: Patrones de Diseño

Los patrones de diseño son soluciones probadas a problemas comunes de arquitectura de software.
Patrones creacionales como Factory y Singleton gestionan el ciclo de vida de los objetos.

```python
class SingletonService:
    _instance = None
    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
```

Patrones estructurales como Adapter y Decorator facilitan la composición flexible.

## Capítulo 3: Sistemas Distribuidos y Microservicios

En sistemas distribuidos, la consistencia eventual y el teorema CAP son consideraciones críticas.
El patrón Saga permite coordinar transacciones distribuidas sin bloqueos en dos fases.

## Capítulo 4: Observabilidad y Monitoreo

La telemetría moderna abarca métricas, trazas distribuidas y registros estructurados.
OpenTelemetry se ha convertido en el estándar unificado para instrumentación de observabilidad.
"""


def test_split_by_tokens():
    sample_markdown_book = get_sample_markdown_book()
    options = SplitOptions(
        mode="tokens",
        target_tokens=80,  # ~320 caracteres
        inject_ai_context=True,
        base_name="manual_arquitectura",
        original_filename="manual_arquitectura.pdf",
        document_title="Manual de Arquitectura de Software",
    )

    result = DocumentSplitter.split_document(sample_markdown_book, options)

    assert len(result.parts) > 1
    assert result.total_characters == len(sample_markdown_book)
    assert result.document_id.startswith("doc_")
    assert result.index_filename == "manual_arquitectura_INDEX.md"

    # Validar primera parte
    part1 = result.parts[0]
    assert part1.part_number == 1
    assert part1.total_parts == len(result.parts)
    assert "part_01_of_" in part1.filename
    assert "---" in part1.content
    assert "document_id:" in part1.content
    assert "previous_part: null" in part1.content
    assert 'next_part: "' in part1.content
    assert "> [!NOTE]" in part1.content

    # Validar última parte
    part_last = result.parts[-1]
    assert part_last.part_number == len(result.parts)
    assert "next_part: null" in part_last.content
    assert 'previous_part: "' in part_last.content


def test_split_by_parts():
    sample_markdown_book = get_sample_markdown_book()
    options = SplitOptions(
        mode="parts",
        num_parts=3,
        inject_ai_context=True,
        base_name="manual",
        original_filename="manual.docx",
    )

    result = DocumentSplitter.split_document(sample_markdown_book, options)

    assert len(result.parts) == 3
    assert result.parts[0].part_number == 1
    assert result.parts[1].part_number == 2
    assert result.parts[2].part_number == 3

    # Validar enlace entre partes consecutivas
    assert result.parts[0].filename in result.parts[1].content
    assert result.parts[1].filename in result.parts[2].content


def test_split_by_headings():
    sample_markdown_book = get_sample_markdown_book()
    options = SplitOptions(
        mode="headings",
        heading_level=2,
        inject_ai_context=True,
        base_name="manual",
        original_filename="manual.pdf",
    )

    result = DocumentSplitter.split_document(sample_markdown_book, options)

    # El documento tiene 1 introducción + 4 capítulos con ##
    assert len(result.parts) >= 4


def test_code_block_integrity():
    sample_markdown_book = get_sample_markdown_book()
    blocks = DocumentSplitter.parse_blocks(sample_markdown_book)

    for block in blocks:
        if "```" in block.text:
            # Si contiene inicio de bloque, debe contener el cierre de bloque
            assert block.text.count("```") % 2 == 0 or block.text.count("```") >= 2


def test_zip_bundle_generation():
    sample_markdown_book = get_sample_markdown_book()
    options = SplitOptions(
        mode="parts",
        num_parts=2,
        inject_ai_context=True,
        base_name="manual_test",
        original_filename="manual_test.pdf",
    )

    result = DocumentSplitter.split_document(sample_markdown_book, options)
    zip_bytes = result.get_zip_bytes()

    assert len(zip_bytes) > 0
    with zipfile.ZipFile(io.BytesIO(zip_bytes), "r") as zf:
        file_list = zf.namelist()
        assert "manual_test_INDEX.md" in file_list
        assert "manual_test_part_01_of_02.md" in file_list
        assert "manual_test_part_02_of_02.md" in file_list

        index_content = zf.read("manual_test_INDEX.md").decode("utf-8")
        assert "# Índice Maestro y Manifiesto de Navegación" in index_content
        assert "Metadatos Globales del Documento" in index_content


def test_save_to_disk():
    sample_markdown_book = get_sample_markdown_book()
    options = SplitOptions(
        mode="parts",
        num_parts=2,
        inject_ai_context=True,
        base_name="disco_test",
        original_filename="disco_test.pdf",
    )

    result = DocumentSplitter.split_document(sample_markdown_book, options)

    with tempfile.TemporaryDirectory() as tmp_dir:
        dest = result.save_to_disk(Path(tmp_dir))
        assert dest.exists()
        assert (dest / "disco_test_INDEX.md").exists()
        assert (dest / "disco_test_part_01_of_02.md").exists()
        assert (dest / "disco_test_part_02_of_02.md").exists()


def test_empty_document():
    options = SplitOptions(base_name="vacio")
    result = DocumentSplitter.split_document("", options)
    assert len(result.parts) == 1
    assert result.total_characters == 0


if __name__ == "__main__":
    print("Ejecutando pruebas de DocumentSplitter...")
    test_split_by_tokens()
    print("  [OK] test_split_by_tokens")
    test_split_by_parts()
    print("  [OK] test_split_by_parts")
    test_split_by_headings()
    print("  [OK] test_split_by_headings")
    test_code_block_integrity()
    print("  [OK] test_code_block_integrity")
    test_zip_bundle_generation()
    print("  [OK] test_zip_bundle_generation")
    test_save_to_disk()
    print("  [OK] test_save_to_disk")
    test_empty_document()
    print("  [OK] test_empty_document")
    print("Todas las pruebas de DocumentSplitter pasaron exitosamente.")

