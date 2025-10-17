import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app

app = create_app()

if __name__ == "__main__":
    # ⚙️ Utilise le port fourni par Railway (par défaut 5000)
    port = int(os.environ.get("PORT", 5000))
    
    # ✅ Écoute sur toutes les interfaces réseau
    app.run(host="0.0.0.0", port=port, debug=True)
