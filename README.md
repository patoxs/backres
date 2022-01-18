# backres
Script python para ser ejecutado dentro de un contenedor

```bash
python3 snapshot
```

Nota: por el momento solo esta para Postgres 12

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
        value: "nombre_pod.namespace"
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
