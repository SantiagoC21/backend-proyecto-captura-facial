from fastapi import FastAPI
from app.database import Base, engine
from app.routers import personas, capturas
from concurrent.futures import ThreadPoolExecutor

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Facial Dataset API",
    description="Backend para captura de rostros con OpenCV",
    version="1.0.0"
)

# Inicializar executor al arrancar
app.state.executor = ThreadPoolExecutor(max_workers=8)

app.include_router(personas.router)
app.include_router(capturas.router)

@app.get("/")
def root():
    return {"mensaje": "API de captura facial activa"}