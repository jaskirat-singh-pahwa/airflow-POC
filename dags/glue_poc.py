import time

from datetime import datetime

from airflow.models import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.amazon.aws.operators.glue import GlueJobOperator

from airflow.hooks.S3_hook import S3Hook


S3_HOOK = S3Hook("s3_conn")

default_args = {
    "start_date": datetime(2022, 3, 13),
    "aws_conn_id": "aws_conn",
    "region_name": "ap-south-1"
}


def create_bucket(bucket_name: str):
    S3_HOOK.create_bucket(bucket_name=bucket_name)


def upload_file_to_s3(filename, key, bucket_name):
    S3_HOOK.load_file(filename, key, bucket_name)
    time.sleep(5)


with DAG(
    dag_id="glue_poc",
    default_args=default_args,
    schedule_interval="@once",
    catchup=False
) as dag:

    create_bucket = PythonOperator(
        task_id="create_bucket",
        python_callable=create_bucket,
        op_kwargs={
            "bucket_name": "test-bucket-for-glue-poc"
        }
    )

    upload_employee_salary_file_to_s3 = PythonOperator(
        task_id="upload_employee_salary_file_to_s3",
        python_callable=upload_file_to_s3,
        op_kwargs={
            "filename": "dags/dataset/employee_salary.csv",
            "key": "employee_salary.csv",
            "bucket_name": "test-bucket-for-glue-poc",
        }
    )

    upload_employee_raise_file_to_s3 = PythonOperator(
        task_id="upload_employee_raise_file_to_s3",
        python_callable=upload_file_to_s3,
        op_kwargs={
            "filename": "dags/dataset/employee_raise.csv",
            "key": "employee_raise.csv",
            "bucket_name": "test-bucket-for-glue-poc",
        }
    )

    glue_job = GlueJobOperator(
        task_id="glue_job",
        job_name="glue_airflow_poc",
        job_desc="This is a POC to trigger Glue job from Airflow",
        script_location="s3://glue-script-poc/glue_task.py",
        script_args={"--name": "Jaskirat", "--age": "25"},
        retry_limit=1,
        iam_role_name="AWSGlueServiceRolePOC",
        s3_bucket="glue-script-poc",
        num_of_dpus=2,
        concurrent_run_limit=1,
        region_name="ap-south-1"
    )

    create_bucket \
        >> [upload_employee_raise_file_to_s3, upload_employee_salary_file_to_s3] \
        >> glue_job
