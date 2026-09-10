from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import Base, engine
from app.routers import personas, capturas
from concurrent.futures import ThreadPoolExecutor

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Facial Dataset API",
    description="Backend para captura de rostros con OpenCV",
    version="1.0.0"
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://faceuni.up.railway.app",  # tu URL real del frontend
        "http://localhost:5173",  # para seguir probando en local
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# Inicializar executor al arrancar
app.state.executor = ThreadPoolExecutor(max_workers=8)

app.include_router(personas.router)
app.include_router(capturas.router)

@app.get("/")
def root():
    return {"mensaje": "API de captura facial activa"}