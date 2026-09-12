"""Print authenticated drilling SVGs without a browser (requires PyMuPDF)."""
import argparse
import hashlib
import json
import re
from pathlib import Path

import pymupdf


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def print_pdf(directory):
    manifest_path = directory/'manifest.json'
    manifest = json.loads(manifest_path.read_text())

    def check():
        for name, sha in manifest['source_sha256'].items():
            if digest(Path(name)) != sha:
                raise ValueError('Drawing source changed: '+name)
        for name, sha in manifest['artifact_sha256'].items():
            if digest(directory/name) != sha:
                raise ValueError('Drawing artifact changed: '+name)

    check()
    output = directory/'drilling.pdf'
    if output.exists():
        raise FileExistsError(output)
    pages = re.findall(r'<svg\b.*?</svg>', (directory/'drilling.html').read_text(), re.DOTALL)
    expected = [(directory/name).read_text().strip()
                for name in manifest['artifact_sha256'] if name.endswith('.svg')]
    if not pages or sorted(pages) != sorted(expected):
        raise ValueError('HTML pages must match the authenticated SVG inventory')
    with pymupdf.open() as pdf:
        for svg in pages:
            with (pymupdf.open(stream=svg.encode(), filetype='svg') as drawing,
                  pymupdf.open(stream=drawing.convert_to_pdf(), filetype='pdf') as source):
                page = pdf.new_page(width=297*72/25.4, height=210*72/25.4)
                page.show_pdf_page(page.rect, source, 0)
        payload = pdf.tobytes(garbage=4, deflate=True)
    check()
    with output.open('xb') as stream:
        stream.write(payload)
    manifest['source_sha256'][str(Path(__file__).relative_to(Path.cwd()))] = digest(Path(__file__))
    manifest['artifact_sha256']['drilling.pdf'] = digest(output)
    manifest['pdf_renderer'] = {'name': 'PyMuPDF', 'version': pymupdf.VersionBind,
                                'page_count': len(pages), 'paper': 'A4 landscape'}
    manifest_path.write_text(json.dumps(manifest, indent=2)+'\n')
    print(f'{output}: {len(pages)} pages')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory', type=Path)
    print_pdf(parser.parse_args().directory)
