"""Main file for starting the server"""
import uvicorn
import argparse

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Run the FastAPI server.")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="Host to run the server on")
    parser.add_argument("--port", type=int, default=8090, help="Port to run the server on")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload")

    args = parser.parse_args()

    uvicorn.run(
        "memsrv.api.main:app",
        host=args.host,
        port=args.port,
        reload=args.reload
    )
