from sqlalchemy import func
from sqlalchemy.types import UserDefinedType, Float

class GeomColType(UserDefinedType):
  """
  Adds ORM support for the GEOMETRY SQL type.
  NOTE: This has only been tested with MySQL.
  """
  def get_col_spec(self):
    """
    Returns the column type in SQL syntax.
    """
    return 'GEOMETRY'

  def bind_expression(self, bindvalue):
    """
    Returns a function to convert the Python value to a SQL Geometry type.
    """
    return func.ST_GeomFromText(bindvalue, type_=self)

  def bind_processor(self, dialect):
    """
    Returns a function that converts a Python value to one that SQL will understand.
    """
    def process(value):
      """
      Converts a Python value to a SQL Geometry string.
      """
      if value is None:
        return None
      # TODO account for POLYGON and MULTIPOLYGON data types
      raise ValueError('NEED TO TODO THIS PART')
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
      Converts a SQL Geometry string to a corresponding Python value depending
      on the actual Geometry type stored in the db.
      """
      if value is None:
        return None
      # TODO account for POLYGON and MULTIPOLYGON data types
      raise ValueError('NEED TO TODO THIS PART')
    return process
