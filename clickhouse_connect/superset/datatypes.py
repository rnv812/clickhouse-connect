import re

from superset.utils.core import GenericDataType
from clickhouse_connect.datatypes.registry import type_map
from clickhouse_connect.datatypes.standard import fixed_string_handling, uint64_handling

type_mapping = (
    (r'^(FLOAT|DECIMAL|INT|UINT)', GenericDataType.NUMERIC),
    (r'^DATE', GenericDataType.TEMPORAL),
    (r'^BOOL', GenericDataType.BOOLEAN)
)


def configure_types():
    # Hack to ensure sqlachemy type information is always imported
    import clickhouse_connect.sqlalchemy
    fixed_string_handling('decode', encoding='utf8', encoding_error='hex')
    uint64_handling('signed')
    compiled = [(re.compile(pattern), gen_type) for pattern, gen_type in type_mapping]
    for name, ch_type_cls in type_map.items():
        for pattern, gen_type in compiled:
            match = pattern.match(name)
            if match:
                ch_type_cls.generic_type = gen_type
                break
        else:
            ch_type_cls.generic_type = GenericDataType.STRING

