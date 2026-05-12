#!/usr/bin/env python
"""Entry point to run ScoobyBench backend"""
import sys
import uvicorn
from app.config import config

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=config.host,
        port=config.port,
        reload=False,
        log_level="info"
    )
