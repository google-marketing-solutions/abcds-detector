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

import logging
from typing import Any

from google.cloud import bigquery
from google.cloud import exceptions as cloud_exceptions

logger = logging.getLogger("abcd_detector")


class BigQueryAPIService:
  """BigQuery service to write data to BigQuery using the specified client."""

  def __init__(self, project_id: str) -> None:
    """Initializes the BigQueryAPIService.

    Args:
      project_id: Google Cloud project ID.
    """
    self.gcs_project_id = project_id

  def _get_full_table_name(self, dataset_name: str, table_name: str) -> str:
    """Generates a full table ID by concatenating project, dataset, and table.

    Args:
      dataset_name: BigQuery dataset name.
      table_name: BigQuery table name.

    Returns:
      Fully qualified table ID string (project.dataset.table).
    """
    return f"{self.gcs_project_id}.{dataset_name}.{table_name}"

  def _get_full_dataset_name(self, dataset_name: str) -> str:
    """Generates a full dataset ID by concatenating project and dataset.

    Args:
      dataset_name: BigQuery dataset name.

    Returns:
      Fully qualified dataset ID string (project.dataset).
    """
    return f"{self.gcs_project_id}.{dataset_name}"

  def create_dataset(self, dataset_name: str, location: str) -> None:
    """Creates a new BigQuery dataset in the specified region.

    Args:
      dataset_name: Name of the dataset to create.
      location: Regional location for the dataset.
    """
    client = bigquery.Client()
    full_dataset_name = self._get_full_dataset_name(dataset_name)
    dataset = bigquery.Dataset(full_dataset_name)
    dataset.location = location
    try:
      dataset = client.create_dataset(dataset, timeout=30)
      dataset_created = bool(dataset and dataset.dataset_id)
      if dataset_created:
        logger.info(
            "The dataset %s was successfully created.", full_dataset_name
        )
    except cloud_exceptions.Conflict:
      logger.info("The dataset %s already exists.", full_dataset_name)

  def create_table(
      self,
      dataset_name: str,
      table_name: str,
      schema: list[bigquery.SchemaField],
  ) -> bool:
    """Creates a new BigQuery table with the provided schema.

    Args:
      dataset_name: Dataset containing the table.
      table_name: Name of the table to create.
      schema: List of BigQuery SchemaField objects defining columns.

    Returns:
      True if the table was created or already exists.
    """
    client = bigquery.Client(project=self.gcs_project_id)
    full_table_name = self._get_full_table_name(dataset_name, table_name)
    table = bigquery.Table(full_table_name, schema=schema)
    try:
      table = client.create_table(table)
      table_created = bool(table and table.full_table_id)
      if table_created:
        logger.info("The table %s was successfully created.", full_table_name)
      return table_created
    except cloud_exceptions.Conflict:
      logger.info("The table %s already exists.", full_table_name)
      return True

  def get_table_by_name(
      self, dataset_name: str, table_name: str
  ) -> bigquery.Table | None:
    """Retrieves a BigQuery table reference by name.

    Args:
      dataset_name: Dataset containing the table.
      table_name: Name of the table to retrieve.

    Returns:
      BigQuery Table object if found, otherwise None.
    """
    client = bigquery.Client()
    full_table_name = self._get_full_table_name(dataset_name, table_name)
    try:
      table = client.get_table(full_table_name)
      return table
    except cloud_exceptions.NotFound:
      logger.warning("Table %s not found!", full_table_name)
      return None

  def delete_table(self, dataset_name: str, table_name: str) -> None:
    """Deletes a BigQuery table with the provided name.

    Args:
      dataset_name: Dataset containing the table.
      table_name: Name of the table to delete.
    """
    client = bigquery.Client()
    full_table_name = self._get_full_table_name(dataset_name, table_name)
    try:
      client.delete_table(full_table_name, not_found_ok=True)
      logger.info("Deleted table %s", full_table_name)
    except cloud_exceptions.NotFound:
      logger.warning("Table %s not found!", full_table_name)

  def load_table_from_dataframe(
      self,
      dataset_name: str,
      table_name: str,
      dataframe: Any,
      schema: list[bigquery.SchemaField],
      write_disposition: str = "WRITE_TRUNCATE",
  ) -> None:
    """Loads a pandas DataFrame into a BigQuery table.

    Args:
      dataset_name: Target dataset name.
      table_name: Target table name.
      dataframe: pandas DataFrame containing rows to load.
      schema: List of BigQuery SchemaField objects.
      write_disposition: BigQuery write disposition strategy.
    """
    client = bigquery.Client(project=self.gcs_project_id)
    full_table_name = self._get_full_table_name(dataset_name, table_name)
    job_config = bigquery.LoadJobConfig(
        schema=schema, write_disposition=write_disposition
    )
    job = client.load_table_from_dataframe(
        dataframe, full_table_name, job_config=job_config
    )
    job.result()
    table = client.get_table(full_table_name)
    if table:
      logger.info(
          "Rows inserted in %s successfully! Total rows in table %s.",
          full_table_name,
          table.num_rows,
      )
    else:
      logger.error(
          "There was an error loading the rows to the table %s. The table"
          " could not be created.",
          full_table_name,
      )
