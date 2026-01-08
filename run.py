import uvicorn

if __name__ == "__main__":
        uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=7004,
        proxy_headers=True,
        forwarded_allow_ips="*",
    )