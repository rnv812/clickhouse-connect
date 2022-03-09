import logging

from typing import Iterable, List, Any

from clickhouse_connect.datatypes import registry
from clickhouse_connect.datatypes.registry import ClickHouseType
from clickhouse_connect.driver.exceptions import DriverError
from clickhouse_connect.driver.rowbinary import read_leb128, read_leb128_str

logger = logging.getLogger(__name__)


def parse_response(source: bytes) -> (List[List[Any]], List[str], List[ClickHouseType]):
    response_size = len(source)
    loc = 0
    num_columns, loc = read_leb128(source, loc)
    logger.debug("Processing response, num columns = %d", num_columns)
    names = []
    for _ in range(num_columns):
        name, loc = read_leb128_str(source, loc)
        names.append(name)
    logger.debug("Processing response, column names = %s", ','.join(names))
    col_types = []
    for _ in range(num_columns):
        col_type, loc = read_leb128_str(source, loc)
        try:
            col_types.append(registry.get_from_name(col_type))
        except KeyError as ke:
            raise DriverError(f"Unknown ClickHouse type returned for type {col_type}")
    logger.debug("Processing response, column ch_types = %s", ','.join([t.name for t in col_types]))
    convs = tuple([t.from_row_binary for t in col_types])
    result = []
    while loc < response_size:
        row = []
        for conv in convs:
            v, loc = conv(source, loc)
            row.append(v)
        result.append(row)
    return result, names, col_types


def build_insert(data: Iterable[Iterable[Any]], *, column_type_names: Iterable[str] = None,
                 column_types: Iterable[ClickHouseType] = None):
    if not column_types:
        column_types = [registry.get_from_name(name) for name in column_type_names]
    convs = tuple([t.to_row_binary for t in column_types])
    output = bytearray()
    for row in data:
        for (value, conv) in zip(row, convs):
            conv(value, output)
    return output