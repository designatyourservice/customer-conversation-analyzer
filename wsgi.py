#!/usr/bin/env python3
"""
WSGI entry point for production deployment
"""

from conversation_analyzer_app import app

if __name__ == "__main__":
    app.run()