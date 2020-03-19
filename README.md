# Flask Online Shop

Api para registro de usuarios y compras de productos en linea.


## Tecnoligias Usadas

* Flask: Web framework
* PyJWT: Para generar WEB token de autentiacion
* SQLAlchemy: Para generar el modelo y usar CRUD a cada uno.
* Flask-Migrate: Generar versiones del modelo de datos.
* sqlite3: Motor de base de datos, se escogio por simplificidad para generar el proyecto
* Werkzeug: Libreria para encriptar datos

## Descripcion de la API

Puede usar [Postman](https://postman.com) para interactuar con los Endpoints

### Uso de la API

La base de datos sin usuarios registrados puede registrar varios usuarios usando
el Endpoint /sign-up, solo hay un administrador de la aplicacion por lo que es necesario
crearlo primero y luego asignale el rol de admin para que pueda agregar, borrar y actualizar
productos de la aplicacion

1. Ir al Endpoint /sign-up y enviar por POST en formato json el usuario administrador

```json
{
  "name": "admin",
  "password": "AnyPassword"
}
```
2. Autenticarse en el sistema en el EndPoint usar Authorization Basic Auth en postman

3. Ejecutar Endpoint /users method PUT usando el usuario de admin para actualizar el rol

### Endpoints

| EndPoint | Metodo | Formato | Variables | Comentatios
|-|-|-|-|-
/invoices/create | POST | json | token |
/sign-up | POST | json | name, password |
/login | GET | Auth | username, password |
/users | PUT | json | token | token usuario admin
/users | GET | json | token | token usuario admin
/users/<id:int> | GET | json | token | acceso a rol admin
/products | GET | | | Sin restriccion
/products/<id:int> | GET | json | token | token del usuario admin
/products/<id:int> | PUT | json | token, products(name, description, price, discount) | token del usuario admin
/products | POST | json | token, products(name, description, price, discount) | acceso a rol admin

### http://4blox.co:5000/invoices/create

Para crear una orden de compra el usuario debe encontrarse autenticado y enviar el TOKEN
por defecto el tiempo de expiracion es 10 min.

Enviar en formato json la lista de productos que el usuario va ordenar.

```json
{
  "products": [
    {"id": 1, "quantity": 2},
    {"id": 2, "quantity": 1}
  ]
}
```

### http://4blox.co:5000/products/<id>

```json
{
  "name": "Nevera Haceb de 200 litros",
  "description": "La mejor nevera",
  "price": 2500000,
  "discount": 10
}
```

