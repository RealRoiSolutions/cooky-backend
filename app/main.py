from fastapi import FastAPI
from app.api.routes import recipes, import_spoonacular, pantry, ingredients, shopping, log, profile
from app.core.config import settings

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # For MVP dev
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(recipes.router, prefix="/recipes", tags=["recipes"])
app.include_router(pantry.router, prefix="/pantry", tags=["pantry"])
app.include_router(ingredients.router, prefix="/ingredients", tags=["ingredients"])
app.include_router(shopping.router, prefix="/shopping-list", tags=["shopping-list"])
app.include_router(log.router, prefix="/log", tags=["log"])
app.include_router(profile.router, prefix="/profile", tags=["profile"])
app.include_router(import_spoonacular.router, prefix="/admin/spoonacular", tags=["admin"])

@app.get("/")
def root():
    return {"message": "Welcome to Cooky API"}
