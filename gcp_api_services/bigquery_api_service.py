#!/usr/bin/env python3

###########################################################################
#
#  Copyright 2024 Google LLC
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      https://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
#
###########################################################################

"""BigQuery service to write data to BigQuery using the specified client."""

from google.cloud import bigquery
from google.cloud import exceptions as cloud_exceptions


class BigQueryAPIService:
  """BigQuery service to write data to BigQuery using the specified client."""

  def __init__(self, project_id):
    self.gcs_project_id = project_id

  def __get_full_table_name(self, dataset_name: str, table_name: str) -> str:
    """Generates a full table name by concatenating project, dataset, and table.
    Args:
      table_name: The name of the table.
    Returns:
      Full table name.
    """
    return self.gcs_project_id + "." + dataset_name + "." + table_name

  def __get_full_dataset_name(self, dataset_name: str) -> str:
    """Generates a full dataset name by concatenating project and dataset
    Args:
      dataset_name: The name of the dataset.
    Returns:
      Full dataset name.
    """
    return self.gcs_project_id + "." + dataset_name

  def create_dataset(self, dataset_name: str, location: str) -> None:
    """Creates a new dataset in the specified region
    Args:
      dataset_name: The name of the dataset to create.
      location: The location where the table will be created
    """
    client = bigquery.Client()
    full_dataset_name = self.__get_full_dataset_name(dataset_name)
    # Construct a full Dataset object to send to the API.
    dataset = bigquery.Dataset(full_dataset_name)
    dataset.location = location
    # Raises google.api_core.exceptions.Conflict if the Dataset already exists
    try:
      # Send the dataset to the API for creation, with an explicit timeout.
      dataset = client.create_dataset(dataset, timeout=30)
      dataset_created = True if dataset and dataset.dataset_id else False
      if dataset_created:
        print(f"The dataset {full_dataset_name} was successfully created. \n")
    except cloud_exceptions.Conflict:
      print(f"The dataset {full_dataset_name} already exists. \n")

  def create_table(
      self,
      dataset_name: str,
      table_name: str,
      schema: list[bigquery.SchemaField],
  ) -> bigquery.Table:
    """Creates a new table with the columns provided.
    Args:
      dataset_name: the dataset containing the table
      table_name: The name of the table to create.
      schema: The schema for the table.
    """
    client = bigquery.Client(project=self.gcs_project_id)
    full_table_name = self.__get_full_table_name(dataset_name, table_name)
    table = bigquery.Table(full_table_name, schema=schema)
    try:
      table = client.create_table(table)
      table_created = True if table and table.full_table_id else False
      if table_created:
        print(f"The table {full_table_name} was successfully created. \n")
      return table_created
    except cloud_exceptions.Conflict:
      print(f"The table {full_table_name} already exists. \n")
      return True

  def get_table_by_name(self, dataset_name: str, table_name: str) -> any:
    """Gets a table by the provided name
    Args:
      dataset_name: The dataset containing the table.
      table_name: The name of the table to delete.
    """
    client = bigquery.Client()
    full_table_name = self.__get_full_table_name(dataset_name, table_name)
    try:
      table = client.get_table(full_table_name)
      return table
    except cloud_exceptions.NotFound:
      print(f"Table {full_table_name} not found!")
      return None

  def delete_table(self, dataset_name: str, table_name: str) -> None:
    """Deletes a table with the provided name
    Args:
      dataset_name: the dataset containing the table
      table_name: The name of the table to delete.
    """
    client = bigquery.Client()
    full_table_name = self.__get_full_table_name(dataset_name, table_name)
    # If the table does not exist, delete_table raises
    # google.api_core.exceptions.NotFound unless not_found_ok is True.
    try:
      client.delete_table(full_table_name, not_found_ok=True)
      print(f"Deleted table {full_table_name}")
    except cloud_exceptions.NotFound:
      print(f"Table {full_table_name} not found!")

  def load_table_from_dataframe(
      self,
      dataset_name: str,
      table_name: str,
      dataframe: any,
      schema: list[bigquery.SchemaField],
      write_disposition: str = "WRITE_TRUNCATE",
  ):
    """Loads the provided dataframe into a BQ table
    Args:
      dataset_name: the dataset containing the table
      table_name: The name of the table to create.
      dataframe: A list of user roles
    """
    client = bigquery.Client(project=self.gcs_project_id)
    full_table_name = self.__get_full_table_name(dataset_name, table_name)
    job_config = bigquery.LoadJobConfig(
        schema=schema, write_disposition=write_disposition
    )
    # Make API request to load data
    job = client.load_table_from_dataframe(
        dataframe, full_table_name, job_config=job_config
    )
    # Wait for the job to complete.
    job.result()
    # Check if table was created
    table = client.get_table(full_table_name)
    if table:
      print(
          f"Rows inserted in {full_table_name} successfully! Total rows in"
          f" table {table.num_rows}. \n"
      )
    else:
      print(
          "There was an error loading the users to the table"
          f" {full_table_name}. The table could not be created."
      )
