#!/usr/bin/env python3
"""prd-manager 文档一致性检查（仅标准库）。

用法:
  check_docs.py [docs/prd]            检查
  check_docs.py [docs/prd] --freeze v1.2.0   为版本写入冻结清单 .freeze.json

规则见 references/lifecycle.md。有 ERROR 时退出码为 1。
"""
import hashlib
import json
import re
import sys
from pathlib import Path

STATUSES = ["草案", "待评审", "已确认", "开发中", "已验收", "已发布", "已取代", "已取消", "已归档"]
VER_RE = re.compile(r"^v\d+\.\d+\.\d+$")
ID_RE = re.compile(r"\b(S|F|Q)(\d+)\b")
RANGE_RE = re.compile(r"\b([SFQ])(\d+)\s*[-–—~～至到]\s*\1?(\d+)\b")

issues = []


def report(level, where, msg):
    issues.append((level, str(where), msg))


def read(p):
    return p.read_text(encoding="utf-8", errors="replace")


def front_matter(text):
    m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    if not m:
        return None
    fm = {}
    for line in m.group(1).splitlines():
        k, _, v = line.partition(":")
        if k.strip() and not line.startswith((" ", "#")):
            fm[k.strip()] = v.split("#")[0].strip()
    return fm


def legacy_status(text):
    m = re.search(r"\*\*状态\*\*\s*[:：]\s*(.+)", text)
    return m.group(1).strip() if m else None


def slug(heading):
    h = heading.strip().lower()
    h = re.sub(r"[^\w\u4e00-\u9fff\- ]", "", h)
    return h.replace(" ", "-")


def anchors(text):
    return {slug(m.group(1)) for m in re.finditer(r"^#{1,6}\s+(.+?)\s*$", text, re.M)}


def defined_ids(text):
    """返回 {id: 行文本}：表格首列或 'S1：' 标题定义的 ID。"""
    out = {}
    for line in text.splitlines():
        m = re.match(r"^\|\s*([SFQ]\d+)\s*\|", line)
        if m:
            out.setdefault(m.group(1), []).append(line)
            continue
        m = re.match(r"^#{2,4}\s*([S]\d+)\s*[：:]", line)
        if m:
            out.setdefault(m.group(1), []).append(line)
    return out


def expand_refs(text):
    refs = set()
    for m in RANGE_RE.finditer(text):
        p, a, b = m.group(1), int(m.group(2)), int(m.group(3))
        if a <= b and b - a < 200:
            refs.update(f"{p}{i}" for i in range(a, b + 1))
    for m in ID_RE.finditer(text):
        refs.add(m.group(1) + m.group(2))
    return refs


def check_links(md, root):
    text = read(md)
    text_nocode = re.sub(r"```.*?```", "", text, flags=re.S)
    for m in re.finditer(r"\[[^\]]*\]\(([^)\s]+)\)", text_nocode):
        target = m.group(1)
        if re.match(r"^[a-z]+:", target) or target.startswith("mailto:"):
            continue
        path, _, frag = target.partition("#")
        dest = (md.parent / path).resolve() if path else md
        if not dest.exists():
            report("ERROR", md.relative_to(root.parent), f"链接目标不存在: {target}")
        elif frag and dest.suffix == ".md" and slug(frag) not in anchors(read(dest)):
            report("WARNING", md.relative_to(root.parent), f"锚点未找到: {target}")


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def freeze(vdir):
    files = {str(p.relative_to(vdir)): sha(p) for p in sorted(vdir.rglob("*"))
             if p.is_file() and p.name != ".freeze.json" and p.name != ".DS_Store"}
    (vdir / ".freeze.json").write_text(json.dumps(files, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"已写入 {vdir/'.freeze.json'}（{len(files)} 个文件）")


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    root = Path(args[0] if args else "docs/prd").resolve()
    if not root.is_dir():
        print(f"目录不存在: {root}")
        return 2
    if "--freeze" in sys.argv:
        i = sys.argv.index("--freeze")
        v = sys.argv[i + 1] if i + 1 < len(sys.argv) else ""
        if v in args:
            args.remove(v)
            root = Path(args[0] if args else "docs/prd").resolve()
        vdir = root / v
        if not vdir.is_dir():
            print(f"版本目录不存在: {vdir}")
            return 2
        freeze(vdir)
        return 0

    versions = sorted((d for d in root.iterdir() if d.is_dir() and VER_RE.match(d.name)),
                      key=lambda d: tuple(int(x) for x in d.name[1:].split(".")), reverse=True)

    # README 索引
    readme = root / "README.md"
    listed = []
    if readme.exists():
        rt = read(readme)
        listed = [m.group(1) for m in re.finditer(r"^- `(v\d+\.\d+\.\d+)`", rt, re.M)]
        names = {d.name for d in versions}
        arch = {d.name for d in (root / "_archive").iterdir()} if (root / "_archive").is_dir() else set()
        for v in listed:
            if v not in names and v not in arch:
                report("ERROR", "README.md", f"索引了不存在的版本 {v}")
        for v in names - set(listed):
            report("WARNING", "README.md", f"版本目录 {v} 未出现在索引")
        key = lambda s: tuple(int(x) for x in s[1:].split("."))
        cur = [v for v in listed]
        if cur != sorted(cur, key=key, reverse=True):
            report("WARNING", "README.md", "索引未按版本倒序（当前区与归档区分别倒序时可忽略）")
        check_links(readme, root)
    else:
        report("WARNING", "README.md", "缺少版本索引")

    # 变更日志
    changelog = root / "CHANGELOG.md"
    released = set()
    if changelog.exists():
        released = set(re.findall(r"^## \[v?(\d+\.\d+\.\d+)\]\s*-\s*\d{4}-\d{2}-\d{2}", read(changelog), re.M))
    else:
        report("WARNING", "CHANGELOG.md", "缺少 docs/prd/CHANGELOG.md")

    prev_removed = {}
    all_defs = {}
    for vdir in reversed(versions):  # 从旧到新
        prd = vdir / "prd.md"
        rel = f"{vdir.name}/prd.md"
        if not prd.exists():
            report("WARNING", vdir.name, "缺少 prd.md")
            continue
        text = read(prd)
        fm = front_matter(text)
        if fm is None:
            report("WARNING", rel, "缺少 front matter（旧格式，参见 references/migration.md）")
            status = legacy_status(text)
        else:
            status = fm.get("status")
            if "skill_version" not in fm:
                report("WARNING", rel, "front matter 缺少 skill_version")
            if fm.get("version") and fm["version"] != vdir.name:
                report("ERROR", rel, f"front matter version={fm['version']} 与目录名不一致")
        if status:
            clean = re.sub(r"^[^\w\u4e00-\u9fff]+", "", status)
            first = re.split(r"[\s|/（(]", clean)[0]
            if first not in STATUSES:
                report("WARNING" if fm is None else "ERROR", rel, f"状态不在枚举内: {status}")
            if first == "已发布" and vdir.name[1:] not in released:
                report("ERROR", rel, "状态为已发布，但 CHANGELOG.md 无该版本带日期条目")
            if first != "已发布" and vdir.name[1:] in released:
                report("WARNING", rel, "CHANGELOG 已有带日期条目，但状态不是已发布")
        else:
            report("WARNING", rel, "未找到状态")

        defs = defined_ids(text)
        for i, rows in defs.items():
            if len(rows) > 1 and i[0] != "S":
                report("ERROR", rel, f"ID 重复定义: {i}")
            for line in rows:
                if "已移除" in line:
                    prev_removed[i] = vdir.name
            if i in prev_removed and prev_removed[i] != vdir.name and not any("已移除" in r for r in rows):
                report("ERROR", rel, f"ID {i} 已在 {prev_removed[i]} 移除，不得复用")
            if i in all_defs and any("新增" in r for r in rows) and i[0] != "Q":
                report("WARNING", rel, f"ID {i} 已在 {all_defs[i]} 定义，本版标为“新增”")
            all_defs.setdefault(i, vdir.name)

        # 下游引用
        others = [p for p in vdir.rglob("*.md") if p != prd]
        if others:
            refs = set()
            for p in others:
                refs |= expand_refs(read(p))
            for i, rows in defs.items():
                if i[0] == "F" and i not in refs and not any("已移除" in r for r in rows):
                    report("WARNING", rel, f"{i} 未被 {vdir.name} 下其他文档引用")

        # 链接
        for p in vdir.rglob("*.md"):
            check_links(p, root)

        # 冻结
        fz = vdir / ".freeze.json"
        if fz.exists():
            try:
                saved = json.loads(read(fz))
            except ValueError:
                report("ERROR", f"{vdir.name}/.freeze.json", "无法解析")
                saved = {}
            for f, h in saved.items():
                p = vdir / f
                if not p.exists():
                    report("ERROR", f"{vdir.name}/{f}", "冻结文件已被删除")
                elif sha(p) != h:
                    report("ERROR", f"{vdir.name}/{f}", "冻结文件被修改（已发布版本只允许勘误；勘误后重新 --freeze 并记入 CHANGELOG）")
        elif status and status.startswith("已发布"):
            report("WARNING", vdir.name, "已发布但无 .freeze.json（可用 --freeze 生成）")

    errs = [i for i in issues if i[0] == "ERROR"]
    for lvl, where, msg in sorted(issues, key=lambda x: (x[0] != "ERROR", x[1])):
        print(f"{lvl:7} {where}: {msg}")
    print(f"\n{len(versions)} 个版本，{len(errs)} ERROR，{len(issues)-len(errs)} WARNING")
    return 1 if errs else 0


if __name__ == "__main__":
    sys.exit(main())
