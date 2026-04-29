"""
Golden Data Preparation - Phase 1 Profiler

Ingests Stonex custodian PSV files into Bronze layer (PySpark Parquet).
Handles all 4 file types with variable and multi-line formats.
"""

import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

import click
from pyspark.sql import SparkSession, DataFrame
from pyspark.sql.types import StructType, StructField, StringType, TimestampType
from pyspark.sql.functions import lit, current_timestamp

from smart_reader import read_psv_file


class GoldenPreparer:
    """Ingests PSV files into Bronze layer."""
    
    def __init__(self, spark: Optional[SparkSession] = None):
        """Initialize with optional SparkSession."""
        self.spark = spark or SparkSession.builder \
            .master("local[*]") \
            .appName("golden-prep") \
            .getOrCreate()
    
    def ingest_bronze(
        self,
        file_path: str,
        custodian_id: str,
        file_type: str,
        mode: str = 'auto'
    ) -> str:
        """
        Ingest a custodian PSV file into Bronze layer.
        
        Args:
            file_path: Path to the PSV file
            custodian_id: Custodian identifier (e.g., 'stonex')
            file_type: File type (cash, account, position, rad)
            mode: PSV variant mode ('auto', 'single_line', 'multi_line_dashed', 'multi_line_blank')
        
        Returns:
            Path to output Parquet directory
        
        Raises:
            FileNotFoundError: If input file not found
            ValueError: If file_type not recognized
        """
        # Validate inputs
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Input file not found: {file_path}")
        
        valid_types = ['cash', 'account', 'position', 'rad']
        if file_type not in valid_types:
            raise ValueError(f"Invalid file_type: {file_type}. Must be one of {valid_types}")
        
        # Read raw records using smart_reader
        click.echo(f"Reading {file_path}...")
        records = read_psv_file(file_path, mode=mode)
        click.echo(f"  Loaded {len(records)} records")
        
        if not records:
            raise ValueError(f"No records found in {file_path}")
        
        # Determine max field count for padding
        max_fields = max(len(r) for r in records)
        click.echo(f"  Max fields: {max_fields}")
        
        # Pad all records to max field count
        records_padded = []
        for record in records:
            padded = record + [''] * (max_fields - len(record))
            records_padded.append(tuple(padded))
        
        # Create schema (all StringType at Bronze layer)
        fields = [StructField(f"field_{i:03d}", StringType(), True) for i in range(max_fields)]
        fields.extend([
            StructField("_source_file", StringType(), False),
            StructField("_custodian_id", StringType(), False),
            StructField("_file_type", StringType(), False),
            StructField("_ingested_at", TimestampType(), False),
            StructField("_record_count", StringType(), False),
            StructField("_max_fields", StringType(), False),
        ])
        schema = StructType(fields)
        
        # Create DataFrame from records with metadata
        ingested_at = datetime.now()
        records_with_meta = [
            record + (
                os.path.basename(file_path),
                custodian_id,
                file_type,
                ingested_at,
                str(len(records_padded)),
                str(max_fields)
            )
            for record in records_padded
        ]
        
        df = self.spark.createDataFrame(records_with_meta, schema=schema)
        
        # Output path
        output_path = f"data/bronze/{custodian_id}/{file_type}"
        os.makedirs(output_path, exist_ok=True)
        
        # Write to Parquet
        click.echo(f"Writing to {output_path}...")
        df.coalesce(1).write.mode("overwrite").parquet(output_path)
        
        click.echo(f"✓ Bronze ingestion complete: {output_path}")
        return output_path
    
    def verify_bronze(self, custodian_id: str, file_type: str) -> None:
        """Verify Bronze Parquet was written correctly."""
        path = f"data/bronze/{custodian_id}/{file_type}"
        if not os.path.exists(path):
            click.echo(f"✗ Path not found: {path}")
            return
        
        df = self.spark.read.parquet(path)
        click.echo(f"\nBronze verification: {path}")
        click.echo(f"  Row count: {df.count()}")
        click.echo(f"  Columns: {len(df.columns)}")
        click.echo(f"  Metadata: {df.select('_custodian_id', '_file_type', '_max_fields').first()}")


@click.group()
def cli():
    """Golden Data Preparation CLI."""
    pass


@cli.command()
@click.option('--input', required=True, help='Input PSV file path')
@click.option('--custodian', default='stonex', help='Custodian ID')
@click.option('--file-type', required=True, 
              type=click.Choice(['cash', 'account', 'position', 'rad']),
              help='File type')
@click.option('--mode', default='auto',
              type=click.Choice(['auto', 'single_line', 'multi_line_dashed', 'multi_line_blank']),
              help='PSV format mode')
def ingest(input: str, custodian: str, file_type: str, mode: str):
    """Ingest a custodian PSV file into Bronze layer."""
    try:
        preparer = GoldenPreparer()
        output_path = preparer.ingest_bronze(input, custodian, file_type, mode)
        preparer.verify_bronze(custodian, file_type)
    except Exception as e:
        click.echo(f"✗ Error: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.option('--custodian', default='stonex', help='Custodian ID')
@click.option('--file-type', required=True,
              type=click.Choice(['cash', 'account', 'position', 'rad']),
              help='File type')
def verify(custodian: str, file_type: str):
    """Verify Bronze Parquet output."""
    try:
        preparer = GoldenPreparer()
        preparer.verify_bronze(custodian, file_type)
    except Exception as e:
        click.echo(f"✗ Error: {e}", err=True)
        sys.exit(1)


if __name__ == '__main__':
    cli()
