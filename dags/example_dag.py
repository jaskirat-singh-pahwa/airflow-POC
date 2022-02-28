import pandas as pd

from airflow.models import DAG
from airflow.operators.dummy import DummyOperator
from airflow.operators.python import PythonOperator
from airflow.providers.amazon.aws.operators.s3 import S3CreateBucketOperator

from airflow.hooks.S3_hook import S3Hook
from datetime import datetime


def process_data_from_s3(raw_data):
    data_set = []

    columns = raw_data.split("\n")[0].split(",")

    for row in raw_data.split("\n")[1:]:
        data_set.append(row.split(","))

    print(pd.DataFrame(data=data_set, columns=columns))


def upload_file_to_s3(filename, key, bucket_name):
    s3_hook = S3Hook("my_airflow_conn_S3")
    s3_hook.load_file(filename, key, bucket_name)


def read_file_from_s3(key, bucket_name):
    s3_hook = S3Hook("my_airflow_conn_S3")
    raw_data = s3_hook.read_key(key, bucket_name)
    process_data_from_s3(raw_data=raw_data)


default_args = {
    "start_date": datetime(2022, 2, 25),
    "aws_conn_id": "my_airflow_conn_S3"
}

with DAG(
    dag_id="test_s3_connection",
    default_args=default_args,
    schedule_interval="@once",
    catchup=False
) as dag:

    start_task = DummyOperator(
        task_id="dummy_task"
    )

    create_bucket_task = S3CreateBucketOperator(
        task_id="create_bucket",
        bucket_name="s3bucket-through-airflow-task",
    )

    upload_file_to_s3_task = PythonOperator(
        task_id="upload_file_to_S3",
        python_callable=upload_file_to_s3,
        op_kwargs={
            "filename": "dags/dataset/sample_data.csv",
            "key": "sample_data_through_airflow_task.csv",
            "bucket_name": "s3bucket-through-airflow-task",
        }
    )

    read_file_from_s3_task = PythonOperator(
        task_id="read_file_from_s3",
        python_callable=read_file_from_s3,
        op_kwargs={
            "key": "sample_data_through_airflow_task.csv",
            "bucket_name": "s3bucket-through-airflow-task",
        }
    )

    # download_file_from_s3_task = PythonOperator()


    start_task \
    >> create_bucket_task \
    >> upload_file_to_s3_task \
    >> read_file_from_s3_task \
    # >> download_file_from_s3_task
