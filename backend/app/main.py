from fastapi import FastAPI

app = FastAPI(title="donsend")


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
