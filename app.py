from flask import Flask

# Crear una instancia de la aplicación Flask
app = Flask(__name__)

# Definir rutas y funcionalidades de la aplicación
@app.route('/')
def index():
    return 'Hello, World!'

# Si se ejecuta este archivo directamente, arrancar el servidor de desarrollo
if __name__ == '__main__':
    app.run(debug=True)
