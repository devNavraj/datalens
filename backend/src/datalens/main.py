from fastapi import FastAPI

from datalens import __version__
from datalens.api import router

app = FastAPI(title="DataLens API", version=__version__)
app.include_router(router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "version": __version__}
