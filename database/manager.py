from psycopg2.extras import RealDictCursor
import psycopg2

from utils.shemas import User, Test, TestCategory, TestType

# Класс для работы с БД
class PostgresDBManager:
    def __init__(self, db_name: str, user: str, password: str, host: str = "localhost", port: int = 5432):
        self.connection = psycopg2.connect(
            dbname=db_name,
            user=user,
            password=password,
            host=host,
            port=port
        )
        self.cursor = self.connection.cursor(cursor_factory=RealDictCursor)

    def _execute(self, query: str, params: tuple = ()):
        """Частный метод для выполнения SQL-запросов."""
        self.cursor.execute(query, params)
        self.connection.commit()

    def add_user(self, user: User):
        query = """
        INSERT INTO users (username, password_hash, first_name, last_name, email, phone_number, role)
        VALUES (%s, %s, %s, %s, %s, %s, %s);
        """
        self._execute(query, (user.username, user.password_hash, user.first_name, user.last_name, user.email, user.phone_number, user.role))

    def add_test(self, test: Test):
        query = "INSERT INTO tests (user_id, type_id, score) VALUES (%s, %s, %s);"
        self._execute(query, (test.user_id, test.type_id, test.score))

    def delete_user(self, user_id: int):
        query = "DELETE FROM users WHERE user_id = %s;"
        self._execute(query, (user_id,))

    def update_user(self, user_id: int, **kwargs):
        """Обновляет данные пользователя по user_id"""
        allowed_fields = {"username", "first_name", "last_name", "email", "phone_number", "role"}
        updates = [f"{key} = %s" for key in kwargs if key in allowed_fields]
        values = tuple(kwargs[key] for key in kwargs if key in allowed_fields)

        if not updates:
            return False

        query = f"UPDATE users SET {', '.join(updates)} WHERE user_id = %s"
        self._execute(query, values + (user_id,))
        return True

    def verify_user_credentials(self, username: str, password_hash: str) -> bool:
        """Проверяет, существует ли пользователь с данным логином и хешем пароля"""
        query = "SELECT user_id FROM users WHERE username = %s AND password_hash = %s"
        self.cursor.execute(query, (username, password_hash))
        return bool(self.cursor.fetchone())

    def get_all_test_categories(self) -> list[TestCategory]:
        """Получает список всех категорий тестов"""
        query = "SELECT * FROM test_categories"
        self.cursor.execute(query)
        categories = self.cursor.fetchall()
        return [TestCategory(**category) for category in categories]

    def get_all_test_types(self) -> list[TestType]:
        """Получает список всех типов тестов"""
        query = "SELECT * FROM test_types"
        self.cursor.execute(query)
        test_types = self.cursor.fetchall()
        return [TestType(**test_type) for test_type in test_types]
    
    def close(self):
        """Закрытие соединения с базой данных."""
        self.cursor.close()
        self.connection.close()