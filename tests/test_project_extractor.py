import sys
import tempfile
import shutil
from pathlib import Path

# Asegurar que el directorio raíz esté en sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from thoth_extractor import extract_directory, ExtractionOptions

def test_project_extraction():
    temp_dir = Path(tempfile.mkdtemp())
    out_dir = Path(tempfile.mkdtemp())

    try:
        # Crear estructura de proyecto sintético
        proj_root = temp_dir / "demo_project"
        (proj_root / "src" / "main").mkdir(parents=True)
        (proj_root / "scripts").mkdir(parents=True)
        (proj_root / "config").mkdir(parents=True)
        (proj_root / "node_modules" / "fake_pkg").mkdir(parents=True)
        (proj_root / ".venv" / "bin").mkdir(parents=True)

        # Crear archivos válidos
        (proj_root / "src" / "main" / "Main.java").write_text(
            "package com.demo;\n\npublic class Main {\n    public static void main(String[] args) {\n        System.out.println(\"Hello\");\n    }\n}\n"
        )
        (proj_root / "scripts" / "deploy.sh").write_text(
            "#!/bin/bash\necho \"Desplegando...\"\n"
        )
        (proj_root / "config" / "application.yml").write_text(
            "server:\n  port: 8080\n  env: production\n"
        )
        (proj_root / "analysis.R").write_text(
            "data <- c(10, 20, 30)\nmean(data)\n"
        )

        # Crear archivos que DEBEN ser ignorados
        (proj_root / "node_modules" / "fake_pkg" / "index.js").write_text("console.log('ignore me');")
        (proj_root / ".venv" / "bin" / "python.exe").write_text("fake binary")
        (proj_root / "package-lock.json").write_text("{}")

        # Ejecutar extracción
        res = extract_directory(proj_root, output_base_dir=out_dir)

        print("=== RESULTADOS DE EXTRACCIÓN ===")
        print(f"Proyecto: {res.project_name}")
        print(f"Archivos procesados: {res.total_files}")
        print(f"Líneas totales: {res.total_lines}")
        print(f"Lenguajes detectados: {list(res.language_stats.keys())}")
        print(f"Carpeta de salida: {res.output_dir}")

        # Aserciones
        assert res.total_files == 4, f"Se esperaban 4 archivos, se encontraron {res.total_files}"
        assert "java" in res.language_stats, "Java no fue detectado"
        assert "bash" in res.language_stats, "Bash no fue detectado"
        assert "yaml" in res.language_stats, "YAML no fue detectado"
        assert "r" in res.language_stats, "R no fue detectado"

        # Verificar archivos generados
        assert res.tree_path and res.tree_path.exists(), "TREE.md no fue generado"
        assert res.consolidated_path and res.consolidated_path.exists(), "CONSOLIDATED.md no fue generado"
        assert res.sources_dir and res.sources_dir.exists(), "Directorio sources/ no fue generado"

        # Verificar contenido de TREE.md
        tree_text = res.tree_path.read_text()
        assert "Main.java" in tree_text, "Main.java no aparece en el árbol"
        assert "deploy.sh" in tree_text, "deploy.sh no aparece en el árbol"
        assert "node_modules" not in tree_text, "node_modules NO debería estar en el árbol"
        assert ".venv" not in tree_text, ".venv NO debería estar en el árbol"

        # Verificar estructura en espejo
        assert (res.sources_dir / "src" / "main" / "Main.java.md").exists(), "Main.java.md no existe en espejo"
        assert (res.sources_dir / "scripts" / "deploy.sh.md").exists(), "deploy.sh.md no existe en espejo"

        # Verificar contenido consolidado
        cons_text = res.consolidated_path.read_text()
        assert "FILE: src/main/Main.java" in cons_text
        assert "```java" in cons_text
        assert "```yaml" in cons_text

        print("\n[OK] Todas las pruebas de extracción de carpetas PASARON exitosamente!")

    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)
        shutil.rmtree(out_dir, ignore_errors=True)


def test_zip_extraction():
    import io
    import zipfile
    from thoth_extractor import extract_zip

    out_dir = Path(tempfile.mkdtemp())
    try:
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w") as zf:
            zf.writestr("src/App.java", "public class App {}")
            zf.writestr("scripts/build.sh", "#!/bin/bash\necho ok")
            zf.writestr("node_modules/fake.js", "should be ignored")
            zf.writestr(".git/config", "should be ignored")
        buf.seek(0)

        res = extract_zip(buf, output_base_dir=out_dir, project_name="test_zip_app")
        assert res.total_files == 2, f"Se esperaban 2 archivos, se obtuvieron {res.total_files}"
        assert (res.output_dir / "TREE.md").exists()
        assert (res.output_dir / "CONSOLIDATED.md").exists()
        assert (res.output_dir / "sources" / "src" / "App.java.md").exists()

        print("[OK] Prueba de extracción desde ZIP PASÓ exitosamente!")
    finally:
        shutil.rmtree(out_dir, ignore_errors=True)


if __name__ == "__main__":
    test_project_extraction()
    test_zip_extraction()
