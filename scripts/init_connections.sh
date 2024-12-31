#!/bin/bash

airflow connections add 'flights_db' \
    --conn-type 'postgres' \
    --conn-host 'flights_db' \
    --conn-schema 'flights' \
    --conn-login 'db_user' \
    --conn-password 'db_pass' \
    --conn-port '5432'