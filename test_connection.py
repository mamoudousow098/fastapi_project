#!/usr/bin/env python3
"""Script pour tester la connexion PostgreSQL"""

from sqlalchemy import text
from app.db.session import engine

def test_connection():
    """Teste la connexion à PostgreSQL"""
    try:
        with engine.connect() as conn:
            # Test simple
            result = conn.execute(text("SELECT version()"))
            version = result.fetchone()[0]
            
            print("✅ Connexion PostgreSQL réussie !")
            print(f"📊 Version: {version[:50]}...")
            
            # Tester la base de données
            result = conn.execute(text("SELECT current_database()"))
            db_name = result.fetchone()[0]
            print(f"🗄️  Base de données: {db_name}")
            
            # Tester l'utilisateur
            result = conn.execute(text("SELECT current_user"))
            user = result.fetchone()[0]
            print(f"👤 Utilisateur: {user}")
            
            return True
            
    except Exception as e:
        print(f"❌ Erreur de connexion: {e}")
        return False

if __name__ == "__main__":
    test_connection()