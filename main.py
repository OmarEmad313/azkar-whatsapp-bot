#!/usr/bin/env python3
"""
WhatsApp Azkar Bot - Main Entry Point
"""

import os
from pathlib import Path
from interfaces.cli import main as cli_main


def setup():
    """Setup initial project structure"""
    # Create required directories
    os.makedirs("static/azkar", exist_ok=True)
    os.makedirs("logs", exist_ok=True)
    
    # Create session directory
    whatsapp_session = Path("whatsapp-session")
    whatsapp_session.mkdir(exist_ok=True)


if __name__ == "__main__":
    setup()
    cli_main()