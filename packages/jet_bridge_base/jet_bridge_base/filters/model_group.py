from sqlalchemy import func, sql

from jet_bridge_base.filters.char_filter import CharFilter
from jet_bridge_base.filters.filter import EMPTY_VALUES
from jet_bridge_base.utils.queryset import get_session_engine


def get_query_func_by_name(name, column):
    if name == 'count':
        return func.count(column)
    elif name == 'sum':
        return func.sum(column)
    elif name == 'min':
        return func.min(column)
    elif name == 'max':
        return func.max(column)
    elif name == 'avg':
        return func.avg(column)

date_trunc_options = {
    'microsecond': 'microseconds',
    'millisecond': 'milliseconds',
    'second': 'minute',
    'minute': 'minute',
    'hour': 'hour',
    'day': 'day',
    'week': 'week',
    'month': 'month',
    'quarter': 'quarter',
    'year': 'year'
}

strftime_options = {
    'microseconds': '%Y-%m-%d %H:%i:%s.%f',
    # 'milliseconds': '%Y-%m-%d %H:%i:%s.%f',
    'second': '%Y-%m-%d %H:%i:%s',
    'minute': '%Y-%m-%d %H:%i:00',
    'hour': '%Y-%m-%d %H:00:00',
    'day': '%Y-%m-%d',
    # 'week': '%Y-%m-%d',
    'month': '%Y-%m-01',
    # 'quarter': '%Y-%m-%d',
    'year': '%Y-01-01'
}

def get_query_lookup_func_by_name(session, name, column):
    lookup_params = name.split('_') if name else []

    try:
        if lookup_params[0] == 'date':
            date_group = lookup_params[1]

            if get_session_engine(session) == 'postgresql':
                if date_group in date_trunc_options:
                    return func.date_trunc(date_trunc_options[date_group], column)
            elif get_session_engine(session) == 'mysql':
                if date_group in strftime_options:
                    return func.date_format(column, strftime_options[date_group])
            else:
                if date_group in strftime_options:
                    return func.strftime(strftime_options[date_group], column)
    except IndexError:
        pass

    if name:
        print('Unsupported lookup: {}'.format(name))

    return column


class ModelGroupFilter(CharFilter):

    def filter(self, qs, value):
        if value in EMPTY_VALUES:
            return qs

        x_column = getattr(self.model, value['x_column'])
        y_column = getattr(self.model, value['y_column'])
        y_func = get_query_func_by_name(value['y_func'], y_column)

        if y_func is None:
            return qs.filter(sql.false())

        x_lookup = get_query_lookup_func_by_name(qs.session, value['x_lookup'], x_column)

        whereclause = qs.whereclause
        qs = qs.session.query(x_lookup.label('group'), y_func.label('y_func'))

        if whereclause is not None:
            qs = qs.filter(whereclause)

        return qs.group_by('group').order_by('group')
