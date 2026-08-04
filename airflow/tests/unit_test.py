def test_api_key(api_key):
    assert api_key == "MOCK_KEY1234"

def test_channel_handle(channel_handle):
    assert channel_handle == "MOCK_CHANNEL"

def test_postgres_conn(mock_postgres_conn_vars):
    conn = mock_postgres_conn_vars

    assert conn.login == "mock"
    assert conn.password == "mock"
    assert conn.host == "127.0.0.1"
    assert conn.port == 8829
    assert conn.schema =="mock_db"

def test_dags_integrity(dagbag):
    assert dagbag.import_errors == {}, f"Import errors found: {dagbag.import_errors}"
    print("=========")

    expected_dag_ids = ["produce_json", "update_db", "data_quality"]
    loaded_dag_ids = list(dagbag.dags.keys())
    print("=========")

    for dag_id in expected_dag_ids:
        assert dag_id in loaded_dag_ids, f"DAG {dag_id} is missing"

    assert dagbag.size() == 3

    expected_task_counts = {
        "produce_json": 5,
        "update_db": 3,
        "data_quality": 3
    }
    print("=========")

    for dag_id, dag in dagbag.dags.items():
        expected_count = expected_task_counts[dag_id]
        actual_count = len(dag.tasks)

        assert (
            expected_count == actual_count
        ), f"DAG {dag_id} has {actual_count} tasks, expected {expected_count}"
    