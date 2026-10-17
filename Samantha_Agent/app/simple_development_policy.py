"""Read-only scope checks for narrowly bounded, pure function edits."""
from __future__ import annotations

import ast
import difflib
import hashlib
from pathlib import Path, PurePosixPath
import re
import subprocess

_BUILTINS = frozenset('len str int float bool abs min max sum sorted round range list dict set tuple enumerate zip any all reversed ValueError TypeError'.split())
_METHODS = frozenset('strip lstrip rstrip lower upper casefold split rsplit splitlines join replace startswith endswith format append extend get keys values items add discard count index isdigit isdecimal isalnum isalpha isspace zfill'.split())
_MUTATING = frozenset('append extend add discard'.split())
_BLOCKED_PARTS = ('backup', 'autosave', 'secret', 'credential', 'auth', 'security', 'persist', 'storage', 'receiver', 'deploy', 'release', 'network', 'email', 'calendar', 'transaction', 'checkpoint', 'git_')
_FORBIDDEN = (ast.Import, ast.ImportFrom, ast.Global, ast.Nonlocal, ast.Yield, ast.YieldFrom, ast.Await, ast.AsyncFunctionDef, ast.ClassDef, ast.With, ast.AsyncWith, ast.Delete, ast.Lambda, ast.Try, ast.NamedExpr)
if hasattr(ast, 'Match'):
    _FORBIDDEN += (ast.Match,)
if hasattr(ast, 'TryStar'):
    _FORBIDDEN += (ast.TryStar,)


def _fail(message: str) -> None:
    raise ValueError(message)


def _tracked_file(root: Path, relative: str) -> Path:
    root = Path(root).resolve()
    if not isinstance(relative, str) or '\\' in relative:
        _fail('Neplatná cesta souboru.')
    parts = PurePosixPath(relative).parts
    if not parts or relative.startswith('/') or any(p in ('', '.', '..') for p in relative.split('/')):
        _fail('Cesta musí být relativní bez průchodu adresáři.')
    current = root
    for part in parts:
        current = current / part
        if current.is_symlink():
            _fail('Symbolické odkazy nejsou povoleny.')
    if not current.is_file() or not current.resolve().is_relative_to(root):
        _fail('Soubor není dostupný uvnitř projektu.')
    try:
        result = subprocess.run(['git', '-C', str(root), 'ls-files', '--error-unmatch', '--', relative], capture_output=True, check=False, timeout=10)
    except (OSError, subprocess.SubprocessError):
        _fail('Nelze ověřit sledování souboru Gitem.')
    if result.returncode:
        _fail('Soubor musí být sledovaný Gitem.')
    return current


def _source_path(path: object) -> str:
    if not isinstance(path, str) or not path.startswith('app/') or not path.endswith('.py'):
        _fail('Povoleny jsou pouze Python soubory v app/.')
    lower = path.lower()
    if (any(part in lower for part in _BLOCKED_PARTS)
            or lower.startswith(('app/communication/', 'app/capabilities/', 'app/workflows/', 'app/camino', 'app/codex', 'app/simple_development'))
            or lower in ('app/cockpit.py', 'app/routine_tasks.py', 'app/samantha_agent.py')):
        _fail('Tento soubor vyžaduje hlavního Adama.')
    return path


def _parse(source: str) -> ast.Module:
    try:
        return ast.parse(source)
    except (SyntaxError, ValueError, RecursionError):
        _fail('Zdroj není platný podporovaný Python.')


def _function(tree: ast.Module, name: str) -> ast.FunctionDef:
    matches = [n for n in tree.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name == name]
    if len(matches) != 1 or not isinstance(matches[0], ast.FunctionDef):
        _fail('Vyber jednu vrcholovou synchronní funkci.')
    node = matches[0]
    if node.decorator_list or getattr(node, 'type_params', []):
        _fail('Dekorované funkce vyžadují Adama.')
    return node


def _bounded(source: object) -> str:
    if not isinstance(source, str) or not source.strip() or len(source.encode('utf-8')) > 12000 or len(source.splitlines()) > 100:
        _fail('Funkce přesahuje povolený rozsah.')
    return source


def _pure(node: ast.FunctionDef) -> None:
    """Conservative syntax gate; unknown helpers and external stores are denied."""
    params = {a.arg for a in (*node.args.posonlyargs, *node.args.args, *node.args.kwonlyargs)}
    params.update(a.arg for a in (node.args.vararg, node.args.kwarg) if a)
    locals_ = {n.id for statement in node.body for n in ast.walk(statement) if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Store)}
    if (params | locals_) & _BUILTINS:
        _fail('Překrytí bezpečných vestavěných funkcí není povoleno.')
    for default in (*node.args.defaults, *[d for d in node.args.kw_defaults if d is not None]):
        try:
            ast.literal_eval(default)
        except (ValueError, TypeError, SyntaxError, RecursionError):
            _fail('Výchozí hodnoty musí být konstantní.')
    annotations = [a.annotation for a in (*node.args.posonlyargs, *node.args.args, *node.args.kwonlyargs) if a.annotation]
    annotations.extend(a.annotation for a in (node.args.vararg, node.args.kwarg) if a and a.annotation)
    if node.returns:
        annotations.append(node.returns)
    for annotation in annotations:
        for item in ast.walk(annotation):
            if (isinstance(item, ast.Name) and item.id not in _BUILTINS) or isinstance(item, (ast.Call, ast.Attribute, ast.Lambda, ast.NamedExpr)):
                _fail('Anotace vyžadují kontrolu hlavního Adama.')
    body = ast.Module(body=node.body, type_ignores=[])
    parents = {id(child): parent for parent in ast.walk(body) for child in ast.iter_child_nodes(parent)}
    fresh_locals = set(locals_ - params)
    for item in ast.walk(body):
        if not isinstance(item, ast.Name) or not isinstance(item.ctx, ast.Store):
            continue
        parent = parents.get(id(item))
        value = None
        if isinstance(parent, ast.Assign) and len(parent.targets) == 1 and parent.targets[0] is item:
            value = parent.value
        elif isinstance(parent, ast.AnnAssign) and parent.target is item:
            value = parent.value
        fresh = isinstance(value, (ast.List, ast.Dict, ast.Set, ast.ListComp, ast.DictComp, ast.SetComp))
        fresh = fresh or (isinstance(value, ast.Call) and isinstance(value.func, ast.Name) and value.func.id in {'list', 'dict', 'set'})
        if not fresh:
            fresh_locals.discard(item.id)
    call_attributes = {id(n.func) for n in ast.walk(body) if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)}
    for n in ast.walk(body):
        if isinstance(n, _FORBIDDEN) or isinstance(n, ast.FunctionDef) or (isinstance(n, ast.comprehension) and n.is_async):
            _fail('Funkce obsahuje nepovolenou konstrukci.')
        if isinstance(n, ast.Name):
            if '__' in n.id or (isinstance(n.ctx, ast.Load) and n.id not in params | locals_ | _BUILTINS):
                _fail('Funkce používá nepovolené jméno nebo globální stav.')
        if isinstance(n, ast.Attribute):
            if id(n) not in call_attributes or n.attr not in _METHODS or '__' in n.attr:
                _fail('Nepovolený přístup k atributu.')
        if isinstance(n, (ast.Subscript, ast.Attribute)) and isinstance(n.ctx, (ast.Store, ast.Del)):
            _fail('Zápis do vnějšího objektu není povolen.')
        if isinstance(n, ast.Call):
            if isinstance(n.func, ast.Name):
                if n.func.id not in _BUILTINS:
                    _fail('Volání pomocné funkce vyžaduje Adama.')
            elif isinstance(n.func, ast.Attribute):
                receiver = n.func.value
                if not isinstance(receiver, (ast.Name, ast.Constant, ast.List, ast.Tuple, ast.Dict, ast.Set)):
                    _fail('Nepodporovaný příjemce volání metody.')
                if n.func.attr in _MUTATING:
                    # Every store to a mutable local must create a fresh collection.
                    if not (isinstance(receiver, (ast.List, ast.Dict, ast.Set)) or (isinstance(receiver, ast.Name) and receiver.id in fresh_locals)):
                        _fail('Změna objektu vyžaduje Adama.')
            else:
                _fail('Nepřímá volání nejsou povolena.')
        if isinstance(n, ast.AugAssign):
            _fail('Změna objektu přiřazením vyžaduje Adama.')
    if any('__' in name for name in params | locals_):
        _fail('Speciální jména nejsou povolena.')


def prepare_function_task(root: Path, request: dict) -> dict:
    """Freeze a bounded edit request without writing or exposing the whole file."""
    if not isinstance(request, dict) or set(request) != {'goal', 'path', 'function', 'test_modules'}:
        _fail('Požadavek má neplatná pole.')
    goal = request['goal']
    name = request['function']
    modules = request['test_modules']
    if not isinstance(goal, str) or not goal.strip() or len(goal) > 1200:
        _fail('Cíl musí mít 1 až 1200 znaků.')
    if not isinstance(name, str) or not name.isidentifier() or '__' in name:
        _fail('Neplatné jméno funkce.')
    if not isinstance(modules, list) or not 1 <= len(modules) <= 3 or any(not isinstance(m, str) or not re.fullmatch(r'tests\.test_[A-Za-z0-9_]+', m) for m in modules) or len(set(modules)) != len(modules):
        _fail('Vyber jeden až tři existující testovací moduly.')
    path = _source_path(request['path'])
    file = _tracked_file(root, path)
    for module in modules:
        _tracked_file(root, module.replace('.', '/') + '.py')
    if file.stat().st_size > 400 * 1024:
        _fail('Zdrojový soubor je příliš velký.')
    try:
        data = file.read_bytes()
        source = data.decode('utf-8')
    except (OSError, UnicodeError):
        _fail('Nelze načíst UTF-8 zdroj.')
    if len(data) > 400 * 1024:
        _fail('Zdrojový soubor je příliš velký.')
    tree = _parse(source)
    node = _function(tree, name)
    # Whole-line replacement must never swallow another top-level statement.
    if any(other is not node and other.lineno <= node.end_lineno and other.end_lineno >= node.lineno for other in tree.body):
        _fail('Funkce musí být na samostatných řádcích.')
    snippet = _bounded(''.join(source.splitlines(keepends=True)[node.lineno - 1:node.end_lineno]))
    _pure(node)
    return {'goal': goal.strip(), 'path': path, 'source_path': path, 'function': name, 'test_modules': list(modules), 'source_sha256': hashlib.sha256(data).hexdigest(), 'original_function': snippet, 'start_line': node.lineno, 'end_line': node.end_lineno}


def validate_function_answer(task: dict, answer: dict) -> str:
    """Validate one replacement function and return its exact source."""
    if not isinstance(answer, dict) or set(answer) != {'function_source', 'summary'}:
        _fail('Odpověď má neplatná pole.')
    if not isinstance(answer['summary'], str) or not answer['summary'].strip() or len(answer['summary']) > 400:
        _fail('Shrnutí musí mít 1 až 400 znaků.')
    replacement = _bounded(answer['function_source'])
    original = _function(_parse(task['original_function']), task['function'])
    tree = _parse(replacement)
    updated = _function(tree, task['function'])
    if len(tree.body) != 1 or replacement.splitlines()[:updated.lineno - 1] or any(line.strip() for line in replacement.splitlines()[updated.end_lineno:]):
        _fail('Odpověď smí obsahovat pouze vybranou funkci.')
    if ast.dump(original.args) != ast.dump(updated.args) or ast.dump(ast.Module(body=original.decorator_list, type_ignores=[])) != ast.dump(ast.Module(body=updated.decorator_list, type_ignores=[])) or (ast.dump(original.returns) if original.returns else None) != (ast.dump(updated.returns) if updated.returns else None) or original.type_comment != updated.type_comment or getattr(original, 'type_params', []) != getattr(updated, 'type_params', []):
        _fail('Signatura funkce se nesmí změnit.')
    _pure(original)
    _pure(updated)
    changed = sum(line.startswith(('+ ', '- ')) for line in difflib.ndiff(task['original_function'].splitlines(), replacement.splitlines()))
    if changed > 100:
        _fail('Změna přesahuje sto řádků.')
    return replacement


def build_updated_source(root: Path, task: dict, replacement: str) -> str:
    """Recheck the frozen scope, then splice only its function; never write."""
    current = prepare_function_task(root, {k: task[k] for k in ('goal', 'path', 'function', 'test_modules')})
    for key in ('source_path', 'source_sha256', 'original_function', 'start_line', 'end_line'):
        if current[key] != task[key]:
            _fail('Zdroj se od přípravy změnil; vrať úkol Adamovi.')
    replacement = validate_function_answer(task, {'function_source': replacement, 'summary': 'Ověření náhrady'})
    source = _tracked_file(root, task['path']).read_bytes().decode('utf-8')
    if hashlib.sha256(source.encode('utf-8')).hexdigest() != task['source_sha256']:
        _fail('Zdroj se od přípravy změnil; vrať úkol Adamovi.')
    lines = source.splitlines(keepends=True)
    old = task['original_function']
    newline = '\r\n' if '\r\n' in old else '\n'
    replacement = replacement.replace('\r\n', '\n').replace('\r', '\n').rstrip('\n').replace('\n', newline)
    if old.endswith(('\n', '\r')):
        replacement += newline
    result = ''.join(lines[:task['start_line'] - 1]) + replacement + ''.join(lines[task['end_line']:])
    _parse(result)
    return result
