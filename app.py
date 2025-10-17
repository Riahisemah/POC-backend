if __name__ == "__main__":
    from app import create_app
    import os

    app = create_app()

    # Utiliser le port fourni par Railway ou 5000 par défaut
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
