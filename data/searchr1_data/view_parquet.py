#!/usr/bin/env python3
"""
Parquet 预览和转换工具

- 打印文件路径、是否存在
- 打印 schema（若安装了 pyarrow）
- 打印总行数（若安装了 pyarrow）
- 打印列名
- 打印前 N 行与后 N 行（优先使用 pyarrow 的高效 head，否则回退到 pandas 全量读取）
- 可选转换为 CSV 格式

用法:
  python view_parquet.py /path/to/file1.parquet [/path/to/file2.parquet ...] 
  可选参数：
    --rows 5        (控制预览的行数)
    --to-csv        (转换为 CSV 格式，默认输出到同目录下 .csv 文件)
    --csv-dir DIR   (指定 CSV 输出目录)
"""

from __future__ import annotations

import argparse
import os
import sys
from typing import List, Optional


def try_import_pyarrow():
    try:
        import pyarrow as pa  # type: ignore
        import pyarrow.dataset as ds  # type: ignore
        import pyarrow.parquet as pq  # type: ignore
        return pa, ds, pq
    except Exception:
        return None, None, None


def try_import_pandas():
    try:
        import pandas as pd  # type: ignore
        return pd
    except Exception:
        return None


def print_section(title: str) -> None:
    print("\n" + "=" * 10 + f" {title} " + "=" * 10)


def convert_to_csv(file_path: str, csv_dir: Optional[str] = None) -> str:
    """将 Parquet 文件转换为 CSV 格式"""
    pd = try_import_pandas()
    if pd is None:
        raise ImportError("需要安装 pandas 来进行 CSV 转换")
    
    # 确定输出文件路径
    if csv_dir is None:
        csv_dir = os.path.dirname(file_path)
    
    base_name = os.path.splitext(os.path.basename(file_path))[0]
    csv_path = os.path.join(csv_dir, f"{base_name}.csv")
    
    # 确保输出目录存在
    os.makedirs(csv_dir, exist_ok=True)
    
    # 读取并保存
    df = pd.read_parquet(file_path)
    df.to_csv(csv_path, index=False)
    
    return csv_path


def preview_parquet(file_path: str, num_rows: int = 5, convert_csv: bool = False, csv_dir: Optional[str] = None) -> None:
    print_section("File")
    print(f"Path: {file_path}")
    if not os.path.exists(file_path):
        print("Exists: False")
        return
    print("Exists: True")

    pa, ds, pq = try_import_pyarrow()
    pd = try_import_pandas()

    # Schema & row count via pyarrow when possible
    if pq is not None:
        try:
            pf = pq.ParquetFile(file_path)
            try:
                schema = pf.schema_arrow
            except Exception:
                schema = None
            if schema is not None:
                print_section("Schema (pyarrow)")
                print(schema)
            # Row count from metadata (fast)
            if pf.metadata is not None:
                print_section("Metadata")
                print(f"Num rows: {pf.metadata.num_rows}")
                print(f"Num row groups: {pf.metadata.num_row_groups}")
        except Exception as e:
            print_section("Schema/Metadata")
            print(f"Unable to read schema/metadata via pyarrow: {e}")

    # Columns
    columns_printed = False
    if pq is not None:
        try:
            pf2 = pq.ParquetFile(file_path)
            arrow_schema = getattr(pf2, "schema_arrow", None)
            if arrow_schema is not None:
                columns = [f.name for f in arrow_schema]
                print_section("Columns")
                print(columns)
                columns_printed = True
        except Exception:
            pass

    if not columns_printed and pd is not None:
        try:
            df_tmp = pd.read_parquet(file_path)
            print_section("Columns")
            print(list(df_tmp.columns))
            del df_tmp
            columns_printed = True
        except Exception:
            pass

    # Head/Tail
    showed_head = False
    showed_tail = False

    # Prefer efficient head via pyarrow.dataset
    if ds is not None:
        try:
            dataset = ds.dataset(file_path)
            table_head = ds.Scanner.from_dataset(dataset).head(num_rows)
            print_section(f"Head (pyarrow head {num_rows})")
            try:
                print(table_head.to_pandas())
            except Exception:
                print(table_head)
            showed_head = True
        except Exception:
            pass

    # Tail is not directly supported by pyarrow efficiently; fall back to pandas if available
    if pd is not None:
        try:
            df = pd.read_parquet(file_path)
            if not showed_head:
                print_section(f"Head (pandas head {num_rows})")
                print(df.head(num_rows))
                showed_head = True
            print_section(f"Tail (pandas tail {num_rows})")
            print(df.tail(num_rows))
            showed_tail = True

            # Dtypes & null counts for quick glance
            print_section("Dtypes")
            print(df.dtypes)
            print_section("Null counts")
            try:
                print(df.isna().sum())
            except Exception:
                pass
        except Exception as e:
            if not showed_head:
                print_section("Head/Tail")
                print(f"Unable to read data via pandas: {e}")
    else:
        if not showed_head:
            print_section("Head/Tail")
            print("Neither pyarrow head nor pandas available to preview rows.")
    
    # CSV 转换
    if convert_csv:
        try:
            csv_path = convert_to_csv(file_path, csv_dir)
            print_section("CSV Conversion")
            print(f"Successfully converted to: {csv_path}")
            file_size = os.path.getsize(csv_path)
            print(f"CSV file size: {file_size:,} bytes ({file_size / 1024 / 1024:.2f} MB)")
        except Exception as e:
            print_section("CSV Conversion")
            print(f"Failed to convert to CSV: {e}")



def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Preview and convert Parquet files")
    parser.add_argument("files", nargs="+", help="Parquet file paths to preview")
    parser.add_argument("--rows", type=int, default=5, help="Number of head/tail rows to show")
    parser.add_argument("--to-csv", action="store_true", help="Convert Parquet files to CSV format")
    parser.add_argument("--csv-dir", type=str, help="Directory for CSV output (default: same as input file)")
    return parser.parse_args(argv)


def main(argv: Optional[List[str]] = None) -> int:
    args = parse_args(argv)
    for file_path in args.files:
        preview_parquet(file_path, num_rows=args.rows, convert_csv=args.to_csv, csv_dir=args.csv_dir)
        print("\n" + "-" * 40 + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())


