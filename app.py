from fastapi import FastAPI

app = FastAPI(title="Jira Delivery Insights")


@app.get("/health")
def health():
    return {"status": "ok"}
