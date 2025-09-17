#!/usr/bin/env python3
"""
Pedalboard Effects Chain - Main Entry Point
"""

import sys
import os
import logging
from PyQt6.QtWidgets import QApplication

# Ensure we can import from src package
if __name__ == "__main__":
    # Add parent directory to sys.path so we can import src as a package
    parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.insert(0, parent_dir)

    from src.ui.main_window import MainWindow
else:
    from ui.main_window import MainWindow


def setup_logging():
    """Configure logging for the application"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('pedalboard_effects.log')
        ]
    )


def main():
    """Main application entry point"""
    setup_logging()
    logger = logging.getLogger(__name__)

    logger.info("Starting Pedalboard Effects Chain application")

    # Create QApplication
    app = QApplication(sys.argv)
    app.setApplicationName("Pedalboard Effects Chain")
    app.setApplicationVersion("1.0.0")

    try:
        # Create and show main window
        main_window = MainWindow()
        main_window.show()

        logger.info("Application started successfully")

        # Run the application
        sys.exit(app.exec())

    except Exception as e:
        logger.error(f"Failed to start application: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()