# backres
Script python para ser ejecutado dentro de un contenedor

```bash
python3 snapshot
```

Nota: por el momento solo esta para Postgres 12

Se deben definir las siguientes variables de entorno:

PROJECT
AWS_REGION
SUBNET_DESTINO
REGION_DESTINO
INSTANCE_CLASS

ID_CUENTA
DB_USER
DB_PASSWORD
DB_PORT
DB_DATABASE

DB_HOST_DESTINO
DB_USER_DESTINO
DB_PASSWORD_DESTINO
DB_PORT_DESTINO
DB_DATABASE_DESTINO

Ejemplo de implementacion en pod:

```
apiVersion: v1
kind: Pod
metadata:
  name: backres
  namespace: nombre-namespace
spec:
  serviceAccountName: name_service_account
  containers:
  - name: backres
    image: imagen_registry
    env:
      - name: PROJECT
        value: "lelelele"
      - name: NAME_RDS
        value: "nombre_rds"
      - name: AWS_REGION
        value: "us-west-2"
      - name: INSTANCE_CLASS
        value: "db.t3.medium"
      - name: ID_CUENTA
        value: "AAAAAA111111"
      - name: DB_USER
        value: "user"
      - name: DB_PASSWORD
        value: "passpass"
      - name: DB_PORT
        value: "1111"
      - name: DB_DATABASE
        value: "nombre_base_datos"
      - name: DB_HOST_DESTINO
        value: "host_destino"
      - name: DB_USER_DESTINO
        value: "user_destino"
      - name: DB_PASSWORD_DESTINO
        value: "pass_destino"
      - name: DB_PORT_DESTINO
        value: "1111"
      - name: DB_DATABASE_DESTINO
        value: "name_base_dedatos_destino"
      - name: SUBNET_DESTINO
        value: "default"
      - name: REGION_DESTINO
        value: "us-east-1"    

```
