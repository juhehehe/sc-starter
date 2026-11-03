"""Build the website of the guide from the Markdown in this repository.

    uv run --group docs site/build.py          build into site/_site/, check it
    uv run --group docs site/build.py serve    preview at http://127.0.0.1:8001

Zensical takes its pages only from a folder below its settings, so this
script first copies the pages to site/_src/: LICENSE, docs/, examples/ and
first-jobs/, without what git ignores, so that leftovers of test runs such
as *.out stay out, and from site/ the start page, stylesheet and script. It
also turns the glossary into tooltips. While serve runs, run the first
command again after a change; serve picks up the new copy.
"""

import base64
import hashlib
import html
import re
import shutil
import subprocess
import sys
import tarfile
import urllib.request
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "site"
SRC = SITE / "_src"
OUT = SITE / "_site"
CACHE = SITE / "_cache"
SOURCES = ["LICENSE", "docs", "examples", "first-jobs"]
# The website's own start page, stylesheet and script, from site/.
SITE_SOURCES = ["index.md", "assets"]
GLOSSARY = ROOT / "docs" / "reference" / "glossary.md"
# Outside SRC, so that Zensical does not take it for a page of its own.
TOOLTIPS = SITE / "_tooltips" / "glossary.md"

# Mermaid, which draws the diagrams, and the three fonts, each fetched once
# from npm and checked against the hash npm publishes for it. The files keep
# their names in the folder given; the licence gets a name of its own.
FONTSOURCE = "https://registry.npmjs.org/@fontsource-variable"
PACKAGES = {
    "mermaid-12.2.0.tgz": {
        "url": "https://registry.npmjs.org/mermaid/-/mermaid-12.2.0.tgz",
        "sha512": "w7nr/SFrLO7BaVTs3dQTvYSV6nYSBj0Yy9DjBhsI"
        "JtAcHqRzXSq4Pg32ujHZ/AdWsAMNEvvhbm5dt9E2tOiHzw==",
        "folder": "assets",
        "files": ["dist/mermaid.min.js"],
        "licence": "mermaid-LICENSE.txt",
    },
    "literata-5.3.0.tgz": {
        "url": f"{FONTSOURCE}/literata/-/literata-5.3.0.tgz",
        "sha512": "1Jw7xvOcoGyB83lxB2nG4bfNbqtX2/TTbdh9sHAO"
        "mU064SvmSdulDtA5RBu5JYWf64fdaKX7xU+z3GO1T2bCHA==",
        "folder": "assets/fonts",
        "files": [
            "files/literata-latin-opsz-normal.woff2",
            "files/literata-latin-opsz-italic.woff2",
        ],
        "licence": "literata-OFL.txt",
    },
    "fraunces-5.3.0.tgz": {
        "url": f"{FONTSOURCE}/fraunces/-/fraunces-5.3.0.tgz",
        "sha512": "9BYGySn4AHEJdgp9Z28tQ3X+laJMEOITXkQarZXe"
        "loWQZDq5oOvXJ3kDA8c7MGIfpogIaZfjrQBqmda8POOCKA==",
        "folder": "assets/fonts",
        "files": ["files/fraunces-latin-opsz-normal.woff2"],
        "licence": "fraunces-OFL.txt",
    },
    "jetbrains-mono-5.3.0.tgz": {
        "url": f"{FONTSOURCE}/jetbrains-mono/-/jetbrains-mono-5.3.0.tgz",
        "sha512": "F32xpS2NsGYoQi2ADSkKTgpJj7ozajsGgDJ8woTn"
        "qjmIB+dxDIqImjl4pXZVEExu8UFZ2ndhmX18EBS/hdz3Lw==",
        "folder": "assets/fonts",
        "files": [
            "files/jetbrains-mono-latin-wght-normal.woff2",
            "files/jetbrains-mono-latin-wght-italic.woff2",
        ],
        "licence": "jetbrains-mono-OFL.txt",
    },
}


def package_files(package: dict) -> dict[str, str]:
    """Where each file the site takes from a package goes, below SRC."""
    files = {member: Path(member).name for member in package["files"]}
    files["LICENSE"] = package["licence"]
    return {member: f"{package['folder']}/{name}" for member, name in files.items()}


LIST_ITEM = re.compile(r" *([-*+]|\d{1,9}[.)]) ")
FENCE = re.compile(r" *(```|~~~)")


def not_ignored(folder: Path, names: list[str]) -> list[str]:
    """Return the files under these names in folder that git does not ignore."""
    listed = subprocess.run(
        [
            "git",
            "ls-files",
            "-z",
            "--cached",
            "--others",
            "--exclude-standard",
            "--",
            *names,
        ],
        cwd=folder,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.split("\0")
    return [name for name in listed if name and (folder / name).is_file()]


def copy_sources() -> list[Path]:
    """Copy the pages to SRC, only what changed, and return the Markdown files."""
    wanted = {name: ROOT / name for name in not_ignored(ROOT, SOURCES)}
    wanted |= {name: SITE / name for name in not_ignored(SITE, SITE_SOURCES)}
    for name, source in wanted.items():
        copy = SRC / name
        if not copy.exists() or copy.read_bytes() != source.read_bytes():
            copy.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, copy)
    managed = {
        target
        for package in PACKAGES.values()
        for target in package_files(package).values()
    }
    for copy in SRC.rglob("*"):
        name = copy.relative_to(SRC).as_posix()
        if copy.is_file() and name not in wanted and name not in managed:
            copy.unlink()
    return sorted(source for name, source in wanted.items() if name.endswith(".md"))


def add_packages() -> None:
    """Put the files the site needs from npm into SRC."""
    for name, package in PACKAGES.items():
        archive = CACHE / name
        if not archive.exists():
            CACHE.mkdir(exist_ok=True)
            with urllib.request.urlopen(package["url"], timeout=60) as response:
                archive.write_bytes(response.read())
        digest = hashlib.sha512(archive.read_bytes()).digest()
        if base64.b64encode(digest).decode() != package["sha512"]:
            sys.exit(
                f"{archive} is not the file npm published; delete it and run again."
            )
        with tarfile.open(archive) as tar:
            for member, target in package_files(package).items():
                path = SRC / target
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(tar.extractfile(f"package/{member}").read())


def write_tooltips() -> None:
    """Turn the glossary into abbreviations, which Zensical shows as tooltips.

    Each entry of the glossary is a heading with the term and a paragraph
    that explains it. That paragraph becomes the tooltip for the term, in
    the singular and the plural, written as inside a sentence: in small
    letters, unless it starts with an abbreviation such as SSH or is one of
    the names in the glossary's front matter. The front matter also names
    the terms that get no tooltip.
    """
    text = GLOSSARY.read_text()

    def listed(key: str) -> set[str]:
        found = re.search(rf"^{key}: \[(.*)\]$", text, re.MULTILINE)
        return {term.strip() for term in found.group(1).split(",")} if found else set()

    names, plain = listed("names"), listed("no_tooltip")
    lines = []
    for term, paragraph in re.findall(r"^## (.+)\n\n((?:.+\n?)+)", text, re.MULTILINE):
        if term in plain:
            continue
        if term not in names and not term.split()[0].isupper():
            term = term[0].lower() + term[1:]
        tip = re.sub(r"\[([^]]*)\]\([^)]*\)", r"\1", " ".join(paragraph.split()))
        tip = tip.replace("`", "")
        lines += [f"*[{term}]: {tip}", f"*[{term}s]: {tip}"]
    TOOLTIPS.parent.mkdir(exist_ok=True)
    TOOLTIPS.write_text("\n".join(lines) + "\n")


def misindented(markdown: Path) -> list[str]:
    """Find lists that GitHub shows one way and Zensical another.

    GitHub nests what starts at the column of the item's text, two or three
    spaces in; Zensical only what starts four spaces in per level. So a
    block that starts on its own line, such as a nested item, a code block
    or a paragraph after an empty line, is indented by a multiple of four.
    And where an item holds a second paragraph, Zensical reads the next
    item as more of that paragraph unless an empty line comes between.
    """
    where = markdown.relative_to(ROOT).as_posix()
    problems = []
    in_code = False
    after_blank = True
    paragraph_indent = None  # of a paragraph that began inside an item
    for number, line in enumerate(markdown.read_text().splitlines(), 1):
        indent = len(line) - len(line.lstrip(" "))
        fence = FENCE.match(line)
        item = LIST_ITEM.match(line)
        if in_code:
            in_code = not fence
        elif line.strip():
            if (after_blank or item or fence) and indent % 4:
                problems.append(f"{where}:{number}: indent by a multiple of 4 spaces")
            if item and paragraph_indent is not None and indent < paragraph_indent:
                problems.append(f"{where}:{number}: put an empty line before this item")
            if fence or item:
                paragraph_indent = None
            elif after_blank and indent >= 4:
                paragraph_indent = indent
            in_code = bool(fence)
        if not line.strip():
            paragraph_indent = None
        after_blank = not line.strip()
    return problems


class Page(HTMLParser):
    """Collect the ids of a built page and the links in its text."""

    def __init__(self, text: str):
        """Read the page at once."""
        super().__init__()
        self.ids, self.links = set(), []
        self.in_article = False
        self.feed(text)

    def handle_starttag(self, tag, attrs):
        """Note every id, and every link inside the article."""
        attrs = dict(attrs)
        if "id" in attrs:
            self.ids.add(attrs["id"])
        if tag == "article":
            self.in_article = True
        elif tag == "a" and self.in_article and attrs.get("href"):
            self.links.append(html.unescape(attrs["href"]))

    def handle_endtag(self, tag):
        """Note where the article ends."""
        if tag == "article":
            self.in_article = False


def broken_links() -> list[str]:
    """Find links between pages whose page, file or heading is missing."""
    pages = {path: Page(path.read_text()) for path in OUT.rglob("*.html")}
    problems = []
    for path, page in pages.items():
        for link in page.links:
            parts = urlsplit(link)
            if parts.scheme:
                continue
            target = (path.parent / unquote(parts.path)).resolve()
            if target.is_dir():
                target = target / "index.html"
            where = path.relative_to(OUT).as_posix()
            if not target.exists():
                problems.append(f"{where}: {link}: no such page or file")
            elif (
                parts.fragment
                and target in pages
                and parts.fragment not in pages[target].ids
            ):
                problems.append(f"{where}: {link}: no such heading")
    return problems


def main() -> None:
    """Build the site, or serve it with `serve`, and check its links."""
    serve = sys.argv[1:] == ["serve"]
    if sys.argv[1:] not in ([], ["serve"]):
        sys.exit(__doc__)
    pages = copy_sources()
    add_packages()
    write_tooltips()
    problems = [problem for page in pages for problem in misindented(page)]
    if problems:
        sys.exit("\n".join(problems))
    command = "serve" if serve else "build"
    zensical = [sys.executable, "-m", "zensical", command]
    if not serve:
        shutil.rmtree(OUT, ignore_errors=True)
        # Without --clean, a page whose source did not change comes from the
        # cache, without a change to the glossary's tooltips.
        zensical += ["--strict", "--clean"]
    # Zensical says itself what went wrong, such as a port already in use.
    zensical += ["-f", str(SITE / "zensical.toml")]
    if subprocess.run(zensical, cwd=ROOT).returncode:
        sys.exit(f"Zensical stopped; the settings are in {SITE / 'zensical.toml'}.")
    if not serve:
        problems = broken_links()
        if problems:
            sys.exit("\n".join(problems))
        print(f"{len(pages)} pages, all links found: {OUT}")


if __name__ == "__main__":
    main()
