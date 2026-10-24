"""Owner's Mac controls over the Camino service's authoritative trash ledger."""
import sqlite3
from camino.domain.project_trash import ProjectTrash, TrashError


def production_trash():
    from scripts import camino_service_control as service
    config = service.load_config(service.ROOT)
    return ProjectTrash(config['metadata_db'], config['media_db'], config['media_root'],
        film_roots=(service.ROOT / 'film-projects', service.ROOT.parents[1] / 'CaminoFilmProjects'),
        viewer_root=config['viewer_media_root'])


def project_trash_action(payload, *, trash=None):
    try:
        if not isinstance(payload, dict):
            raise ValueError('Neplatný požadavek.')
        operation = payload.get('operation')
        keys = {'list': set(), 'preview': {'request_id'}, 'restore': {'request_id'},
                'film': {'request_id', 'project_id', 'trip_id'},
                'confirm': {'request_id', 'plan_token', 'confirmation'}}
        if operation not in keys or set(payload) != keys[operation] | {'operation'}:
            raise ValueError('Neplatná pole požadavku.')
        trash = trash or production_trash()
        args = {k: v for k, v in payload.items() if k != 'operation'}
        if operation == 'list':
            return {'ok': True, 'requests': trash.listing()}
        if operation == 'film':
            result = trash.request_film(**args)
        elif operation == 'confirm':
            result = trash.confirm(args['request_id'], args['plan_token'], args['confirmation'])
        else:
            result = getattr(trash, operation)(**args)
        return {'ok': True, 'request': result}
    except (TrashError, ValueError, OSError, KeyError, sqlite3.DatabaseError) as error:
        return {'ok': False, 'error': getattr(error, 'code', 'trash_unavailable'),
                'message': str(error) if isinstance(error, ValueError) else 'Koš teď nelze bezpečně ověřit.'}
