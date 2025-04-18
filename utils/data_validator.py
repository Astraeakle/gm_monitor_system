import re
from datetime import datetime

class DataValidator:
    @staticmethod
    def validate_date_format(date_str, format='%Y-%m-%d'):
        """Valida que una cadena tenga el formato de fecha correcto"""
        try:
            datetime.strptime(date_str, format)
            return True
        except ValueError:
            return False
    
    @staticmethod
    def validate_time_format(time_str, format='%H:%M:%S'):
        """Valida que una cadena tenga el formato de hora correcto"""
        try:
            datetime.strptime(time_str, format)
            return True
        except ValueError:
            return False
    
    @staticmethod
    def validate_email(email):
        """Valida un formato de correo electronico"""
        pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
        return bool(re.match(pattern, email))
    
    @staticmethod
    def validate_non_empty(value):
        """Valida que un valor no esté vacío"""
        if value is None:
            return False
        if isinstance(value, str) and value.strip() == '':
            return False
        return True
    
    @staticmethod
    def validate_numeric(value):
        """Valida que un valor sea numérico"""
        try:
            float(value)
            return True
        except (ValueError, TypeError):
            return False
    
    @staticmethod
    def validate_range(value, min_val, max_val):
        """Valida que un valor esté dentro de un rango"""
        try:
            num_val = float(value)
            return min_val <= num_val <= max_val
        except (ValueError, TypeError):
            return False