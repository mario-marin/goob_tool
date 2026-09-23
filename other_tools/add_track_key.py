#!/usr/bin/env python3
"""
Tool to add or remove keys in every track entry in tracks.json.
Supports nested keys (e.g., "metadata.duration") and multiple value types.
"""

import json
import sys
import os


def load_tracks(filepath: str) -> dict:
    """Load tracks from a JSON file."""
    if not os.path.exists(filepath):
        print(f"Error: File '{filepath}' not found.")
        sys.exit(1)
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


def save_tracks(filepath: str, data: dict) -> None:
    """Save tracks to a JSON file."""
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"Saved to '{filepath}'.")


def set_nested_key(obj: dict, key_path: str, value) -> None:
    """
    Set a value in a nested dict using a dot-separated key path.
    E.g., key_path="metadata.duration" sets obj["metadata"]["duration"] = value.
    Creates intermediate dicts as needed.
    """
    keys = key_path.split(".")
    current = obj
    for key in keys[:-1]:
        if key not in current or not isinstance(current[key], dict):
            current[key] = {}
        current = current[key]
    current[keys[-1]] = value


def get_nested_key(obj: dict, key_path: str):
    """
    Get a value from a nested dict using a dot-separated key path.
    Returns None if the path doesn't exist.
    """
    keys = key_path.split(".")
    current = obj
    for key in keys:
        if isinstance(current, dict) and key in current:
            current = current[key]
        else:
            return None
    return current


def delete_nested_key(obj: dict, key_path: str) -> bool:
    """
    Delete a key from a nested dict using a dot-separated key path.
    E.g., key_path="metadata.duration" deletes obj["metadata"]["duration"].
    Returns True if the key was found and deleted, False otherwise.
    """
    keys = key_path.split(".")
    current = obj
    for key in keys[:-1]:
        if isinstance(current, dict) and key in current:
            current = current[key]
        else:
            return False
    if isinstance(current, dict) and keys[-1] in current:
        del current[keys[-1]]
        return True
    return False


def prompt_value(value_type: str):
    """Prompt the user to enter a value based on the chosen type."""
    if value_type == "string":
        val = input("Enter string value (leave empty for ''): ").strip()
        return val
    elif value_type == "number":
        val = input("Enter number (leave empty for 0): ").strip()
        if val == "":
            return 0
        try:
            if "." in val:
                return float(val)
            return int(val)
        except ValueError:
            print("Invalid number, defaulting to 0.")
            return 0
    elif value_type == "boolean":
        val = input("Enter boolean (true/false, leave empty for false): ").strip().lower()
        if val == "true":
            return True
        return False
    elif value_type == "array":
        val = input("Enter comma-separated items (leave empty for []): ").strip()
        if val == "":
            return []
        return [item.strip() for item in val.split(",") if item.strip()]
    elif value_type == "object":
        val = input("Enter JSON object (leave empty for {}): ").strip()
        if val == "":
            return {}
        try:
            return json.loads(val)
        except json.JSONDecodeError:
            print("Invalid JSON, defaulting to {}.")
            return {}
    return None


def main():
    filepath = input("Path to tracks.json (default: ../tim-tams-viewer/public/data/tracks.json): ").strip()
    if not filepath:
        filepath = "../tim-tams-viewer/public/data/tracks.json"

    data = load_tracks(filepath)

    if "tracks" not in data or not isinstance(data["tracks"], list):
        print("Error: 'tracks' key not found or is not a list.")
        sys.exit(1)

    # Show existing keys in the first track for reference
    if data["tracks"]:
        existing_keys = list(data["tracks"][0].keys())
        print(f"\nExisting keys in track entries: {', '.join(existing_keys)}")

    # Prompt for operation type
    print("\nOperations:")
    print("  1. add    - Add a new key to every track")
    print("  2. remove - Remove a key from every track")
    op_map = {"1": "add", "2": "remove"}
    op_choice = input("\nChoose operation (1-2): ").strip()
    operation = op_map.get(op_choice, "add")

    # Prompt for the key path
    if operation == "add":
        key_path = input("\nNew key path (dot-separated for nesting, e.g. 'metadata.duration'): ").strip()
    else:
        key_path = input("\nKey path to remove (dot-separated for nesting, e.g. 'metadata.duration'): ").strip()
    if not key_path:
        print("Error: Key path cannot be empty.")
        sys.exit(1)

    if operation == "add":
        # Check if key already exists in first track
        if get_nested_key(data["tracks"][0], key_path) is not None:
            print(f"Warning: Key '{key_path}' already exists in the first track entry.")
            overwrite = input("Overwrite? (y/n): ").strip().lower()
            if overwrite != "y":
                print("Aborted.")
                sys.exit(0)

        # Prompt for value type
        print("\nValue types:")
        print("  1. string  - A text value")
        print("  2. number  - An integer or float")
        print("  3. boolean - true or false")
        print("  4. array   - A list of items")
        print("  5. object  - A JSON object")
        type_map = {"1": "string", "2": "number", "3": "boolean", "4": "array", "5": "object"}
        type_choice = input("\nChoose type (1-5): ").strip()
        value_type = type_map.get(type_choice)
        if not value_type:
            print("Invalid choice. Defaulting to string.")
            value_type = "string"

        # Prompt for the actual value
        value = prompt_value(value_type)

        # Apply to all tracks
        count = len(data["tracks"])
        print(f"\nAdding '{key_path}' = {json.dumps(value, ensure_ascii=False)} to {count} tracks...")
        for track in data["tracks"]:
            set_nested_key(track, key_path, value)

    elif operation == "remove":
        # Check if key exists in first track
        if get_nested_key(data["tracks"][0], key_path) is None:
            print(f"Warning: Key '{key_path}' does not exist in the first track entry.")
            confirm = input("Still remove from all tracks? (y/n): ").strip().lower()
            if confirm != "y":
                print("Aborted.")
                sys.exit(0)

        count = len(data["tracks"])
        print(f"\nRemoving '{key_path}' from {count} tracks...")
        for track in data["tracks"]:
            delete_nested_key(track, key_path)

    save_tracks(filepath, data)
    print("Done!")


if __name__ == "__main__":
    main()