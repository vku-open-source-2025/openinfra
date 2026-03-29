#!/usr/bin/env python3
"""
Admin Credential Generator
Generate secure credentials for admin users.
"""
import secrets
import string
import sys


def generate_strong_password(length=20):
    """Generate a cryptographically strong password."""
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*()-_=+"
    password = ''.join(secrets.choice(alphabet) for _ in range(length))
    return password


def generate_username(prefix="admin"):
    """Generate unique admin username."""
    return f"{prefix}_{secrets.token_hex(4)}"


def generate_jwt_secret():
    """Generate JWT secret key."""
    return secrets.token_urlsafe(32)


def main():
    print("=" * 80)
    print("🔐 SECURE CREDENTIAL GENERATOR")
    print("=" * 80)
    
    # Generate credentials
    username = generate_username()
    password = generate_strong_password(20)
    jwt_secret = generate_jwt_secret()
    
    print("\n📋 ADD TO .env FILE:")
    print("-" * 80)
    print(f"ADMIN_USERNAME={username}")
    print(f"ADMIN_PASSWORD={password}")
    print(f"JWT_SECRET_KEY={jwt_secret}")
    print("-" * 80)
    
    # Password strength
    print("\n✅ PASSWORD STRENGTH ANALYSIS:")
    print(f"   Length: {len(password)} characters")
    print(f"   Uppercase: {'✓' if any(c.isupper() for c in password) else '✗'}")
    print(f"   Lowercase: {'✓' if any(c.islower() for c in password) else '✗'}")
    print(f"   Digits: {'✓' if any(c.isdigit() for c in password) else '✗'}")
    print(f"   Symbols: {'✓' if any(c in '!@#$%^&*()-_=+' for c in password) else '✗'}")
    
    print("\n⚠️  SECURITY WARNINGS:")
    print("   1. Save credentials in a password manager")
    print("   2. Never commit .env file to git")
    print("   3. Rotate credentials every 90 days")
    print("   4. Use different passwords for different environments")
    
    print("\n" + "=" * 80)


if __name__ == "__main__":
    main()
