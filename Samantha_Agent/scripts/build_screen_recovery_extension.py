#!/usr/bin/env python3
"""Build the reviewed, dependency-free local VS Code extension as a VSIX."""

import argparse
import json
from pathlib import Path
import zipfile
from xml.sax.saxutils import escape


SOURCE = Path(__file__).resolve().parents[1] / "tools/vscode-screen-recovery"


def build(output):
    package = json.loads((SOURCE / "package.json").read_text())
    manifest = f'''<?xml version="1.0" encoding="utf-8"?>
<PackageManifest Version="2.0.0" xmlns="http://schemas.microsoft.com/developer/vsx-schema/2011">
<Metadata><Identity Language="en-US" Id="{escape(package['name'])}" Version="{escape(package['version'])}" Publisher="{escape(package['publisher'])}"/>
<DisplayName>{escape(package['displayName'])}</DisplayName><Description xml:space="preserve">{escape(package['description'])}</Description>
<Properties><Property Id="Microsoft.VisualStudio.Code.Engine" Value="{escape(package['engines']['vscode'])}"/><Property Id="Microsoft.VisualStudio.Code.ExtensionKind" Value="ui"/></Properties>
</Metadata><Installation><InstallationTarget Id="Microsoft.VisualStudio.Code"/></Installation><Dependencies/>
<Assets><Asset Type="Microsoft.VisualStudio.Code.Manifest" Path="extension/package.json" Addressable="true"/></Assets>
</PackageManifest>'''
    content_types = '''<?xml version="1.0" encoding="utf-8"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="json" ContentType="application/json"/><Default Extension="cjs" ContentType="application/javascript"/><Default Extension="md" ContentType="text/markdown"/><Default Extension="vsixmanifest" ContentType="text/xml"/></Types>'''
    with zipfile.ZipFile(output, "x", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("extension.vsixmanifest", manifest)
        archive.writestr("[Content_Types].xml", content_types)
        for name in ("package.json", "extension.cjs", "README.md"):
            archive.write(SOURCE / name, f"extension/{name}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path, help="New .vsix file; existing files are never overwritten")
    args = parser.parse_args()
    build(args.output)
    print("Local Screen Recovery VSIX built.")
