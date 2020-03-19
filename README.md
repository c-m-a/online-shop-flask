# Flask Online Shop

Api para registro de usuarios y compras de productos en linea.


## Tecnoligias Usadas

* Flask
* PyJWT: Para generar WEB token de autentiacion
* SQLAlchemy: Para generar el modelo y usar CRUD a cada uno.
* Flask-Migrate: Generar versiones del modelo de datos.
* sqlite3: Motor de base de datos, se escogio por simplificidad para generar el proyecto

## Descripcion de la API

Puede usar (Postman)[https://postman.com] para interactuar con los Endpoints

### Endpoints

EndPoint | Metodo | Formato | Variables | Comentatios
-|-|-
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



