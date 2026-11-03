// Small marks on each page, set before Zensical builds its tooltips.

// Each code block says where it belongs, by its title: a command for your
// computer or the cluster, output that is not for typing, or the content of
// a file. The pages write only the title, ```bash title="Your computer"```,
// which GitHub shows as a plain code block; the class lets the stylesheet
// add the icon.
// R stands for the console of R, which runs on your computer.
const kinds = {
  "Your computer": "computer",
  R: "computer",
  Cluster: "cluster",
  Output: "output",
};

for (const title of document.querySelectorAll(".highlight > .filename")) {
  const kind = kinds[title.textContent.trim()] ?? "file";
  title.parentElement.classList.add(`where-${kind}`);
}

// The READMEs of the examples write a check as a paragraph that starts with
// **Check:**, followed by the code blocks of the check (a command, the
// output to expect), so that GitHub shows it plainly. Here they become one
// Check box, as on the pages in docs/.
for (const label of document.querySelectorAll("article p > strong:first-child")) {
  const paragraph = label.parentElement;
  if (paragraph.firstChild !== label || label.textContent.trim() !== "Check:") {
    continue;
  }
  const box = document.createElement("div");
  box.className = "admonition check";
  const title = document.createElement("p");
  title.className = "admonition-title";
  title.textContent = "Check";
  paragraph.before(box);
  label.remove();
  const start = paragraph.firstChild;
  if (start?.nodeType === Node.TEXT_NODE) {
    start.textContent = start.textContent.trimStart();
  }
  box.append(title, paragraph);
  while (box.nextElementSibling?.matches(".highlight")) {
    box.append(box.nextElementSibling);
  }
}

// A task page starts with a line such as
// **Time:** 45–75 min · **Waiting:** hours to days for your account,
// which GitHub shows as bold labels. Here each part becomes a span of its
// own, so that the stylesheet can put a clock before the time and an
// hourglass before the waiting. The labels stay, without their colons.
const metaParts = { "Time:": "meta-time", "Waiting:": "meta-waiting" };

for (const label of document.querySelectorAll("article p > strong:first-child")) {
  const paragraph = label.parentElement;
  if (paragraph.firstChild !== label || label.textContent.trim() !== "Time:") {
    continue;
  }
  const parts = [];
  for (const node of [...paragraph.childNodes]) {
    const kind = metaParts[node.nodeName === "STRONG" ? node.textContent.trim() : ""];
    if (kind) {
      const part = document.createElement("span");
      part.className = kind;
      const name = document.createElement("span");
      name.className = "meta-label";
      name.textContent = node.textContent.trim().replace(/:$/, "");
      part.append(name);
      parts.push(part);
    } else {
      const part = parts.at(-1);
      if (node.nodeType === Node.TEXT_NODE) {
        // The dot between the parts goes; the stylesheet sets the space.
        let text = node.textContent.replace(/\s*·\s*$/, " ");
        if (part.childNodes.length === 1) {
          text = text.trimStart();
        }
        node.textContent = text;
      }
      part.append(node);
    }
  }
  paragraph.classList.add("meta");
  paragraph.replaceChildren(...parts);
}

// On the glossary itself, a term in another entry links to its own entry
// instead of showing a tooltip, once per entry; elsewhere it keeps its
// tooltip.
const slug = (text) => text.toLowerCase().replace(/[^a-z0-9]+/g, "-");

if (location.pathname.endsWith("/glossary/")) {
  const linked = new Set();
  for (const term of document.querySelectorAll("article abbr[title]")) {
    const words = term.textContent;
    const entry = [slug(words), slug(words.replace(/s$/, ""))]
      .map((id) => document.getElementById(id))
      .find((heading) => heading?.matches("h2"));
    let own = term.closest("p, li");
    while (own && own.tagName !== "H2") {
      own = own.previousElementSibling;
    }
    const pair = `${own?.id} ${entry?.id}`;
    if (entry && entry !== own && !linked.has(pair)) {
      linked.add(pair);
      const link = document.createElement("a");
      link.href = `#${entry.id}`;
      link.textContent = words;
      term.replaceWith(link);
    }
  }
}
