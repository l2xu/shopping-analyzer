"""
Lidl Receipt Data Updater - Entry Point

This is the main entry point for the shopping analyzer application.
For first-time setup or complete refresh, choose option 1.
For monthly updates (adds only new data and sorts by date), choose option 2.

Usage:
    python get_data.py              # Interactive menu
    python get_data.py initial      # Run initial setup
    python get_data.py update       # Run update
"""

import sys

from cli import main
from workflows import initial_setup, update_data


if __name__ == "__main__":
    """
    Entry point for the script. Provides a menu interface for users.
    """
    # Check for command line arguments for backwards compatibility
    if len(sys.argv) > 1:
        if sys.argv[1] == "initial":
            initial_setup()
        elif sys.argv[1] == "update":
            update_data()
        else:
            print(f"Unknown argument: {sys.argv[1]}")
            print("Usage: python get_data.py [initial|update]")
    else:
        # Run interactive menu
        main()
