import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "memsrv.api.main:app",
        host="0.0.0.0",
        port=8090,
        reload=True
    )