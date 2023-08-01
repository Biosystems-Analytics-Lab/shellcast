from sqlalchemy import func
from sqlalchemy.types import UserDefinedType, Float

class PointColType(UserDefinedType):
  """
  Adds ORM support for the POINT SQL type.
  NOTE: This has only been tested with MySQL.
  """
  def get_col_spec(self):
    """
    Returns the column type in SQL syntax.
    """
    return 'POINT'

  def bind_expression(self, bindvalue):
    """
    Returns a function to convert the Python value to a SQL Geometry Point type.
    """
    return func.ST_PointFromText(bindvalue, type_=self)

  def bind_processor(self, dialect):
    """
    Returns a function that converts a Python value to one that SQL will understand.
    """
    def process(value):
      """
      Converts a tuple, (lat, lng), to a SQL Point string, 'POINT(lng lat)'.
      """
      if value is None:
        return None
      assert isinstance(value, tuple)
      lat, lng = value
      return 'POINT(%s %s)' % (lng, lat)
    return process

  def column_expression(self, col):
    """
    Returns a function to use on the raw SQL Geometry Point type when retrieving a value from the db.
    """
    return func.ST_AsText(col, type_=self)

  def result_processor(self, dialect, coltype):
    """
    Returns a function that converts an SQL value to a Python value.
    """
    def process(value):
      """
      Converts a SQL Point string, POINT(lng lat), to a tuple, (lat, lng).
      """
      if value is None:
        return None
      lng, lat = value[6:-1].split() # 'POINT(135.00 35.00)' => ('135.00', '35.00')
      return (float(lat), float(lng))
    return process
