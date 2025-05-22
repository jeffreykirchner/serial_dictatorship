echo "Dump Database"
pg_dump --host=localhost --port=5432 --username=dbadmin --dbname=serial_dictatorship --file=database_dumps/serial_dictatorship.sql -v -Fc