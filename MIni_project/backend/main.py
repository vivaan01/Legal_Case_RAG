from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api.routes import router as api_router
from backend.core.settings import get_settings


def create_app() -> FastAPI:
	settings = get_settings()
	app = FastAPI(title=settings.app_name)
	app.add_middleware(
		CORSMiddleware,
		allow_origins=["*"],
		allow_credentials=True,
		allow_methods=["*"],
		allow_headers=["*"],
	)

	@app.get("/")
	def root():
		excluded = {"/openapi.json", "/docs", "/docs/oauth2-redirect", "/redoc"}
		endpoints = sorted(
			{route.path for route in app.routes if getattr(route, "methods", None) and route.path not in excluded}
		)
		return {
			"message": "Legal Case RAG API",
			"endpoints": endpoints,
		}

	app.include_router(api_router)
	return app


app = create_app()

