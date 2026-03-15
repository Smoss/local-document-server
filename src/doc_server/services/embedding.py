import httpx

from doc_server.config import settings


class OllamaEmbedder:
    def __init__(
        self,
        base_url: str = settings.ollama_url,
        model: str = settings.ollama_model,
    ):
        self.base_url = base_url
        self.model = model
        self._client = httpx.AsyncClient(base_url=base_url, timeout=60.0)

    async def embed(self, text: str) -> list[float]:
        results = await self.embed_batch([text])
        return results[0]

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        response = await self._client.post(
            "/api/embed",
            json={"model": self.model, "input": texts},
        )
        response.raise_for_status()
        data = response.json()
        return data["embeddings"]

    async def is_available(self) -> bool:
        try:
            response = await self._client.get("/api/tags")
            return response.status_code == 200
        except httpx.ConnectError:
            return False

    async def close(self):
        await self._client.aclose()
