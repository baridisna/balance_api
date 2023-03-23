from drf_yasg import openapi

def date_filter_schema(method):
    schema = []
    if method == 'GET':
        schema = [
            openapi.Parameter(
                'from_date',
                openapi.IN_QUERY,
                required=False,
                type=openapi.TYPE_STRING,
                description='filter by from date(example: 2023-01-19)'
            ),
            openapi.Parameter(
                'end_date',
                openapi.IN_QUERY,
                required=False,
                type=openapi.TYPE_STRING,
                description='filter by end date(example: 2023-01-19)'
            ),
            openapi.Parameter(
                'page',
                openapi.IN_QUERY,
                required=False,
                type=openapi.TYPE_INTEGER,
                description='page pagination'
            ),
        ]
    return schema
