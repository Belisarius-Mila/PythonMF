"""One guarded Standard turn over the existing client connection; no daemon."""
from app import recovery_guide_trial as calibration
from app.recovery_guide_sources import canonical_json


class StandardTurn:
    def __init__(self, inner, *, context, request, instructions, before_send):
        self.inner, self.context, self.request_spec = inner, context, request
        self.instructions, self.before_send = instructions, before_send
        self.thread_id = self.turn_id = None
        self.start_attempted = self.attempted = False
        self.unexpected_items = set()

    def __getattr__(self, name):
        return getattr(self.inner, name)

    def receive(self, predicate, **kwargs):
        return calibration.StandardOneTurn.receive(self, predicate, **kwargs)

    def request(self, method, params):
        if method == 'thread/start':
            if self.start_attempted:
                raise ValueError('anchor_second_thread')
            self.start_attempted = True
            if (params.get('cwd') != str(self.context.resolve())
                    or params.get('model') != calibration.MODEL
                    or params.get('ephemeral') is not True
                    or params.get('approvalPolicy') != 'never'
                    or params.get('sandbox') != 'read-only'
                    or params.get('baseInstructions') != self.instructions
                    or params.get('developerInstructions') != self.instructions):
                raise ValueError('anchor_thread_scope_changed')
            config = {**params.get('config', {}),
                **{'features.' + n: False for n in calibration.DISABLED_FEATURES}}
            reply = self.inner.request(method, {**params, 'config': config})
            sandbox = reply.get('sandbox', {})
            if (reply.get('cwd') != str(self.context.resolve())
                    or reply.get('model') != calibration.MODEL
                    or reply.get('approvalPolicy') != 'never'
                    or sandbox.get('type') != 'readOnly'
                    or sandbox.get('networkAccess', False) is not False):
                raise ValueError('anchor_effective_permissions_unconfirmed')
            thread = reply.get('thread', {}).get('id')
            if not isinstance(thread, str) or not thread:
                raise ValueError('anchor_missing_thread_id')
            self.thread_id = thread
            return reply
        if method == 'turn/start':
            if self.attempted or not self.thread_id or params.get('threadId') != self.thread_id:
                raise ValueError('anchor_second_or_foreign_turn')
            if (params.get('model') != calibration.MODEL or params.get('effort') != 'medium'
                    or params.get('approvalPolicy') != 'never'
                    or params.get('sandboxPolicy') != {'type': 'readOnly', 'networkAccess': False}
                    or params.get('input') != [{'type': 'text', 'text': canonical_json(self.request_spec.payload)}]
                    or params.get('outputSchema') != self.request_spec.schema
                    or 'serviceTier' in params or 'serviceTierForTurn' in params):
                raise ValueError('anchor_turn_scope_changed')
            self.attempted = True
            self.before_send(self.thread_id)  # Persistent marker MUST succeed before wire.
            reply = self.inner.request(method, {**params, 'serviceTierForTurn': 'default'})
            self.turn_id = reply.get('turn', {}).get('id')
            return reply
        if method not in {'config/read', 'skills/list'}:
            raise ValueError('anchor_rpc_outside_scope')
        return self.inner.request(method, params)
