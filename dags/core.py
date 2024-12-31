from airflow.providers.postgres.hooks.postgres import PostgresHook


def get_data_from_postgres(
        postgres_conn_id, 
        sql_script):
    hook = PostgresHook(postgres_conn_id=postgres_conn_id)
    conn = hook.get_conn()

    cursor = conn.cursor()
    cursor.execute(sql_script)

    columns = [desc[0] for desc in cursor.description]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]