"""Record build artifacts inside the new image; verify untouched upstream files."""
import hashlib
import json
import re
import subprocess
import tarfile
from pathlib import Path


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    root = Path('/opt/ccx-upstream-2.21')
    source = root/'source.tar.bz2'
    source_files = {}
    with tarfile.open(source) as archive:
        for item in archive.getmembers():
            if item.isfile():
                original = archive.extractfile(item).read()
                path = root/item.name
                if path.read_bytes() != original:
                    raise ValueError('Upstream source changed: '+item.name)
                source_files[item.name] = hashlib.sha256(original).hexdigest()
    binaries = [Path('/usr/bin/ccx'), Path('/usr/local/bin/ccx-upstream-2.21')]
    linked = {str(binary): subprocess.check_output(['ldd', str(binary)], text=True) for binary in binaries}
    libraries = {Path(p).resolve() for text in linked.values() for p in re.findall(r'(/\S+)\s+\(', text)}
    report = {'upstream_source_archive_sha256': sha(source), 'upstream_files_sha256': source_files,
              'binary_sha256': {str(p): sha(p) for p in binaries},
              'linked_library_sha256': {str(p): sha(p) for p in sorted(libraries)}, 'ldd': linked,
              'compiler_versions': {name: subprocess.check_output([name, '--version'], text=True) for name in ('gcc', 'gfortran', 'make')},
              'packages': subprocess.check_output(['dpkg-query', '-W'], text=True),
              'build_support_sha256': {name: sha(root/name) for name in ('Makefile.upstream', 'record_build.py', 'Dockerfile')},
              'qualification': 'Unmodified upstream2.21 source; separate build-system adaptation and executable; packaged ccx preserved. Not observer or physical validation.'}
    (root/'build_manifest.json').write_text(json.dumps(report, indent=2)+'\n')


if __name__ == '__main__':
    main()
