class LuxContext:
    def __init__(self):
        self._injected = {}
        self._relations = set()

    def inject(self, key, value):
        self._injected[key] = value

    def get(self, key, default=None):
        return self._injected.get(key, default)

    async def call(self, alias, *args, **kwargs):
        from lux.registry import GeneRegistry  # załóżmy że istnieje
        from get_gene(alias) import get_gene  # funkcja do pobierania genów
        gene = GeneRegistry.get(alias)
        if not gene:
            raise Exception(f"Gene '{alias}' not found")
        return await gene(self, *args, **kwargs)

    async def execute(self, alias, *args, **kwargs):
        # Można tu dodać routing, bezpieczeństwo, permissiony itd.
        if alias not in self._relations:
            raise PermissionError(f"'{alias}' is not in related permissions")
        return await self.call(alias, *args, **kwargs)

    def relate(self, alias):
        self._relations.add(alias)

    async def emit(self, event: dict):
        socket = self.get("event_socket")
        if socket:
            await socket.send(event)
