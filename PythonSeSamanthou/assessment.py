"""Shared, declarative checks for offline lessons; course data is never evaluated."""
import ast


AST_KINDS = {name: getattr(ast, name) for name in
             ('Mult', 'For', 'If', 'FunctionDef', 'Add', 'Sub', 'Div', 'Return', 'While')}
CHECK_KINDS = {'output_lines', 'variables_equal', 'uses_name', 'ast_kind', 'drawing_equals'}


def validate_checks(checks):
    if not isinstance(checks, list) or not checks:
        raise ValueError('Lekce musí mít alespoň jedno pravidlo kontroly.')
    for check in checks:
        if not isinstance(check, dict) or set(check) != {'kind', 'value'}:
            raise ValueError('Pravidlo kontroly musí obsahovat kind a value.')
        kind, value = check['kind'], check['value']
        if kind not in CHECK_KINDS:
            raise ValueError(f'Neznámý typ kontroly: {kind!r}.')
        if kind == 'ast_kind' and (not isinstance(value, str) or value not in AST_KINDS):
            raise ValueError('Nepodporovaná konstrukce Pythonu v kontrole.')
        if kind == 'uses_name' and (not isinstance(value, str) or not value.isidentifier()):
            raise ValueError('Kontrola používá neplatné jméno proměnné.')
        if kind == 'output_lines' and (not isinstance(value, list) or
                                      not all(isinstance(x, str) for x in value)):
            raise ValueError('Očekávaný výpis musí být seznam řádků.')
        if kind == 'variables_equal' and (not isinstance(value, dict) or not value or
                                         not all(isinstance(k, str) and k.isidentifier() for k in value)):
            raise ValueError('Očekávané proměnné musí být pojmenované hodnoty.')
        if kind == 'drawing_equals':
            arities = {'circle': 5, 'rect': 6, 'line': 6, 'text': 5, 'background': 2}
            if not isinstance(value, list) or any(
                    not isinstance(shape, list) or not shape or not isinstance(shape[0], str)
                    or len(shape) != arities.get(shape[0]) for shape in value):
                raise ValueError('Neplatná očekávaná kresba.')


def assess_lesson(lesson, source, result):
    if result['error']:
        return False, 'Nejdřív oprav chybu, kterou najdeš v záložce Výpis.'
    try:
        nodes = list(ast.walk(ast.parse(source)))
    except SyntaxError:
        return False, 'Nejdřív oprav chybu, kterou najdeš v záložce Výpis.'
    for check in lesson['checks']:
        kind, value = check['kind'], check['value']
        if kind == 'output_lines':
            passed = result['output'].strip().splitlines() == value
        elif kind == 'variables_equal':
            passed = all(k in result['variables'] and result['variables'][k] == v
                         for k, v in value.items())
        elif kind == 'uses_name':
            passed = any(isinstance(n, ast.Name) and isinstance(n.ctx, ast.Load)
                         and n.id == value for n in nodes)
        elif kind == 'ast_kind':
            passed = any(isinstance(n, AST_KINDS[value]) for n in nodes)
        elif kind == 'drawing_equals':
            passed = result['commands'] == value
        else:
            raise ValueError(f'Neznámý typ kontroly: {kind!r}.')
        if not passed:
            return False, lesson['feedback']
    return True, lesson['success']
