from fastapi import FastAPI
from routers import dashboard, authentication,upload, applications, reports,processing, profile, settings


app=FastAPI(title="PUDA SCRUTNY APPLICATION")
app.include_router(authentication.router)
app.include_router(dashboard.router)
app.include_router(upload.router)
app.include_router(applications.router)
app.include_router(reports.router)
app.include_router(processing.router)
app.include_router(profile.router)
app.include_router(settings.router)