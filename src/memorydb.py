class InMemoryDB:
    def __init__(self):
        self._collections = {}

    def collection(self, name):
        return InMemoryCollection(self._collections.setdefault(name, {}))

class InMemoryCollection:
    def __init__(self, store):
        self.store = store

    def document(self, doc_id=None):
        if doc_id is None:
            import uuid
            doc_id = str(uuid.uuid4())
        return InMemoryDoc(self.store, doc_id)

    def where(self, field=None, op=None, value=None, *, filter=None):
        if filter is not None:
            field = filter.field_path
            op = filter.op_string
            value = filter.value
        return InMemoryQuery(self.store, field, op, value)

    def limit(self, n):
        return InMemoryQuery(self.store, None, None, None, limit=n)

    def stream(self):
        return [InMemoryDoc(self.store, doc_id) for doc_id in self.store]

class InMemoryDoc:
    def __init__(self, store, doc_id):
        self.store = store
        self.id = doc_id
        self.reference = self  # Firestore compatibility

    # Firestore-like API
    @property
    def exists(self):
        return self.id in self.store

    def get(self, key=None, default=None):
        if key is None:
            return self
        return self.store.get(self.id, {}).get(key, default)

    def to_dict(self):
        return dict(self.store.get(self.id, {}))

    def set(self, data):
        self.store[self.id] = dict(data)

    def update(self, data):
        self.store.setdefault(self.id, {}).update(data)

    def delete(self):
        self.store.pop(self.id, None)


class InMemoryQuery:
    def __init__(self, store, field, op, value, limit=None):
        self.store = store
        self.field = field
        self.op = op
        self.value = value
        self._limit = limit

    def limit(self, n):
        self._limit = n
        return self

    def _match(self, data):
        if self.field is None:
            return True

        v = data.get(self.field)

        if self.op == '==':
            return v == self.value
        if self.op == '!=':
            return v != self.value
        if self.op == 'in':
            return v in self.value
        if self.op == 'not-in':
            return v not in self.value

        return False

    def stream(self):
        results = []
        for doc_id, data in self.store.items():
            if self._match(data):
                results.append(InMemoryDoc(self.store, doc_id))
                if self._limit and len(results) >= self._limit:
                    break
        return results