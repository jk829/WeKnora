"""验证镜像中已安装技能的 Python 源码是否有效。

在目录权限设置完成后，以普通执行用户在沙箱中运行，使用实际调用技能的解释器：
    python3 - <skill-dir> <script> [<script> ...] [--optional <script> ...]

此过程不执行技能代码，也不判断导入是否可解析。导入检查已刻意移除：
脚本可能通过条件插入、同级模块常量、环境变量或辅助函数修改 sys.path，
静态分析无法穷举，近似判断会拒绝实际可运行的技能。拒绝安装会丢弃已经成功的
依赖安装，并继续使用旧镜像。安装智能体拥有 root shell 和真实解释器，
应由它执行导入来验证，而不是在这里猜测。

这里只检查文件层面可以确定的事项：执行用户能否读取所有源码、源码能否解析，
以及清单中声明的发行包是否已安装到虚拟环境。

诊断结果分级：
    stdout 的 note: 行仅作提示，保留镜像。
    stderr 的问题行会拒绝安装。
    退出码 0：可以保留镜像。
    退出码 1：存在无法通过安装包解决的问题，如语法错误或源码不可读。
    退出码 2：全部问题均为缺失依赖，可再交给安装智能体修复一轮。

--optional 之后的文件接受相同检查，但问题仅作为提示。技能正常执行不应加载
测试或示例，随包附带的 tests/ 目录不应决定安装是否成功。
"""

import ast
import os
import re
import sys

OPTIONAL_FLAG = "--optional"

EXIT_UNREPAIRABLE = 1
EXIT_MISSING_DEPENDENCY = 2

root = os.path.abspath(sys.argv[1])
_argv_scripts = sys.argv[2:]
if OPTIONAL_FLAG in _argv_scripts:
    _cut = _argv_scripts.index(OPTIONAL_FLAG)
    entry_scripts = _argv_scripts[:_cut]
    optional_scripts = _argv_scripts[_cut + 1 :]
else:
    entry_scripts = _argv_scripts
    optional_scripts = []
all_scripts = entry_scripts + optional_scripts
optional_set = set(optional_scripts)

# 问题会拒绝安装；提示仅报告，仍保留镜像。
problems = []
notes = []

# 记录是否存在无法通过安装依赖解决的问题。该状态
# 决定退出码，供调用方判断再执行一轮安装是否
# 有帮助，或是否必须修改技能包本身。
unrepairable = False


def add_problem(message, repairable=False):
    global unrepairable
    if message not in problems:
        problems.append(message)
    if not repairable:
        unrepairable = True


def add_note(message):
    if message not in notes:
        notes.append(message)


def note_instead_of_problem(message, repairable=False):
    """报告辅助文件的检查结果，但不影响安装结论。

    为兼容 add_problem 接口接收 repairable 参数，但忽略它；提示不改变退出码。
    """
    add_note("%s (auxiliary file; this does not fail the install)" % message)


def distribution_name(raw):
    """返回依赖行声明的发行包名称，无法识别时返回空字符串。

    -r、-e、--index-url 等选项、VCS URL、本地路径和归档不直接声明发行包；
    不能猜造包名，否则可能因已满足的依赖而错误拒绝安装。
    """
    line = raw.split("#")[0].strip()
    if not line or line.startswith("-"):
        return ""
    name = re.split(r"[\s<>=!~;\[@]", line)[0].strip()
    if not re.match(r"^[A-Za-z0-9][A-Za-z0-9._-]*$", name):
        return ""
    return name


def marker_of(raw):
    """返回依赖行中的 PEP 508 环境标记；不存在时返回空字符串。"""
    _, _, marker = raw.split("#")[0].partition(";")
    return marker.strip()


def marker_applies(marker):
    """判断 pip 是否会在当前镜像中安装具有该环境标记的依赖。

    无法确定时返回 None；调用方应视为无法强制校验，而非缺失。版本必须按
    版本语义比较，因此仅使用 packaging 评估；手工字符串比较会将 3.10 判为
    小于 3.9，从而拒绝 pip 已正确解析的依赖。基础虚拟环境通常没有 packaging，
    因此返回 None 很常见。
    """
    if re.search(r"\bextra\b", marker):
        # 依赖受 extra 限制，只有显式请求该 extra 时 pip 才会安装。
        return False
    try:
        from packaging.markers import Marker
    except Exception:
        return None
    try:
        return bool(Marker(marker).evaluate())
    except Exception:
        return None


def load_pyproject(path):
    try:
        import tomllib
    except ImportError:
        return None
    try:
        with open(path, "rb") as handle:
            return tomllib.load(handle)
    except Exception:
        return None


def declared_requirement_lines():
    """从 requirements.txt 和 pyproject.toml 生成 (来源, 依赖行) 对。"""
    requirements = os.path.join(root, "requirements.txt")
    if os.path.isfile(requirements):
        with open(requirements, encoding="utf-8", errors="replace") as handle:
            for line in handle:
                yield "requirements.txt", line
    pyproject = os.path.join(root, "pyproject.toml")
    if not os.path.isfile(pyproject):
        return
    data = load_pyproject(pyproject)
    if not data:
        return
    for item in data.get("project", {}).get("dependencies") or []:
        if isinstance(item, str):
            yield "pyproject.toml", item
    poetry = ((data.get("tool") or {}).get("poetry") or {}).get("dependencies") or {}
    if isinstance(poetry, dict):
        for name, spec in poetry.items():
            if str(name).strip().lower() == "python":
                continue
            # 包含 optional、markers 或 Python 版本约束的
            # 表格式依赖是条件依赖，Poetry 不会在当前环境
            # 无条件安装它。
            if isinstance(spec, dict) and (
                spec.get("optional") or spec.get("markers") or spec.get("python")
            ):
                continue
            yield "pyproject.toml", str(name)


def check_declared_requirements():
    """检查清单是否声明了虚拟环境中缺失的发行包。

    这是对安装要求的直接检查：声明了应安装的包而 pip 未装上，才算失败。
    pip 应跳过的依赖，如环境标记不满足或受 extras 限制，仅报告提示。
    例如在 Linux 上不能因 pywin32; sys_platform == "win32" 未安装而拒绝技能。
    """
    try:
        from importlib import metadata
    except ImportError:
        return
    for source, raw in declared_requirement_lines():
        name = distribution_name(raw)
        if not name:
            continue
        try:
            metadata.distribution(name)
            continue
        except Exception:
            pass
        missing = "%s declares %s but it is not installed in %s" % (
            source,
            name,
            sys.prefix,
        )
        marker = marker_of(raw)
        if not marker:
            add_problem(missing, repairable=True)
            continue
        applies = marker_applies(marker)
        if applies:
            add_problem(missing, repairable=True)
        elif applies is None:
            add_note(
                "%s, and its environment marker '%s' cannot be evaluated here, "
                "so it is not enforced" % (missing, marker)
            )


for relative in all_scripts:
    report = note_instead_of_problem if relative in optional_set else add_problem
    script = os.path.join(root, relative)
    try:
        with open(script, "rb") as source:
            code = source.read()
    except OSError as exc:
        report("%s cannot be read by the skill execution user (%s)" % (relative, exc))
        continue
    try:
        ast.parse(code, filename=relative)
    except SyntaxError as exc:
        report("%s has a syntax error on line %s: %s" % (relative, exc.lineno, exc.msg))

check_declared_requirements()

for note in notes:
    sys.stdout.write("note: %s\n" % note)

if problems:
    sys.stderr.write("\n".join(problems) + "\n")
    sys.exit(EXIT_UNREPAIRABLE if unrepairable else EXIT_MISSING_DEPENDENCY)

print(
    "verified %d python file(s) against %s"
    % (len(all_scripts), sys.executable or "python3")
)
