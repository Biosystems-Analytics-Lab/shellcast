#!/usr/bin/env python3
"""
Generate a secure secret key for ShellCast applications.
This key should be used consistently across all applications (notification system and web apps).
"""

import secrets


def generate_secret_key():
    """Generate a secure secret key for the application"""
    return secrets.token_hex(32)


def main():
    """Main function to generate and display the secret key"""
    secret_key = generate_secret_key()

    print("=" * 60)
    print("ShellCast Secret Key Generator")
    print("=" * 60)
    print(f"Generated SECRET_KEY: {secret_key}")
    print()
    print("Add this to your config.ini under [Web] section:")
    print(f"SECRET_KEY = {secret_key}")
    print()
    print("Also add the same key to your web application configurations:")
    print("- shellcast-web-nc/config.py")
    print("- shellcast-web-sc/config.py")
    print("- shellcast-web-fl/config.py")
    print("=" * 60)


if __name__ == "__main__":
    main()
