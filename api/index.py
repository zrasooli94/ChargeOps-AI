from app.main import app

# Vercel serves this FastAPI function under /api/*
app.root_path = "/api"
