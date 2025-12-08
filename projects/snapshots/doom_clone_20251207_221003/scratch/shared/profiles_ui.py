class UIProfileManager:
    def __init__(self):
        self.profiles = {}
        self.current_id = None

    def save(self, pid, payload):
        if pid in self.profiles and self.profiles[pid] != payload:
            raise ValueError('Conflict')
        self.profiles[pid] = payload
        if self.current_id is None:
            self.current_id = pid
        return pid

    def load(self, pid):
        if pid not in self.profiles:
            raise KeyError('NotFound')
        return self.profiles[pid]

    def delete(self, pid):
        if pid not in self.profiles:
            raise KeyError('NotFound')
        del self.profiles[pid]
        if self.current_id == pid:
            self.current_id = None if not self.profiles else next(iter(self.profiles))
        return True

    def bootstrap(self):
        if self.profiles:
            raise RuntimeError('Already bootstrapped')
        self.profiles['default'] = {'name': 'Default User'}
        self.current_id = 'default'
        return self.profiles['default']
