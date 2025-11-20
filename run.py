from app import create_app

app = create_app()

if __name__ == '__main__':
    # debug=True is fine for dev; not for production
    app.run(debug=True)