from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    """
    Преобразует пароль в хэш.
    """
    return pwd_context.hash(password)


def verify_password(entered_password: str, hashed_password: str):
    """
    Проверяет соответствие паролей
    """
    return pwd_context.verify(entered_password, hashed_password)