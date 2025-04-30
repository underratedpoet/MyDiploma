from datetime import datetime, timedelta

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
        try:
            self.cursor.execute(query, params)
            self.connection.commit()
        except psycopg2.Error as e:
            self.connection.rollback()
            raise e

    def fetch_one(self, query: str, params: tuple = ()):
        """Выполняет SQL-запрос и возвращает одну запись."""
        self.cursor.execute(query, params)
        return self.cursor.fetchone()

    def user_exists(self, username: str, email: str) -> bool:
        """Проверяет, существует ли пользователь с таким username или email."""
        query = "SELECT user_id FROM users WHERE username = %s OR email = %s"
        self.cursor.execute(query, (username, email))
        return bool(self.cursor.fetchone())

    def add_user(self, user: User):
        """Добавляет нового пользователя, если он не существует."""
        if self.user_exists(user.username, user.email):
            return False  # Пользователь уже существует

        query = """
        INSERT INTO users (username, password_hash, first_name, last_name, email, phone_number, role)
        VALUES (%s, %s, %s, %s, %s, %s, %s);
        """
        self._execute(query, (user.username, user.password_hash, user.first_name, user.last_name, user.email, user.phone_number, user.role))
        return True  # Пользователь успешно добавлен

    def verify_user_credentials(self, username: str, password_hash: str) -> dict | None:
        """Проверяет существование пользователя с данным логином и хэшем пароля."""
        query = "SELECT username, email, role FROM users WHERE username = %s AND password_hash = %s"
        return self.fetch_one(query, (username, password_hash))

    def get_user_by_username(self, username: str):
        """Получает данные пользователя по его `username`"""
        query = "SELECT user_id, username, first_name, last_name, email, phone_number, role FROM users WHERE username = %s;"
        self.cursor.execute(query, (username,))
        user = self.cursor.fetchone()
        return user if user else None
    
    def get_tests_by_user(self, username: str, time_after: datetime):
        """Получает данные о тестах, пройденных пользователем, по его `username` и за указанное время"""
        query = "SELECT type_id, score, t.created_at, difficulty FROM tests t, users u WHERE u.user_id = t.user_id AND u.username = %s AND t.created_at > %s;"
        self.cursor.execute(query, (username, time_after))
        tests = self.cursor.fetchall()
        return tests if tests else None        
    
    def update_user(self, username: str, user: User) -> bool:
        """Обновляет данные пользователя, кроме пароля."""
        fields = []
        values = []

        if user.first_name is not None:
            fields.append("first_name = %s")
            values.append(user.first_name)

        if user.last_name is not None:
            fields.append("last_name = %s")
            values.append(user.last_name)

        if user.email is not None:
            fields.append("email = %s")
            values.append(user.email)

        if user.phone_number is not None:
            fields.append("phone_number = %s")
            values.append(user.phone_number)

        if not fields:
            return False  # Если нет данных для обновления

        query = f"UPDATE users SET {', '.join(fields)} WHERE username = %s;"
        values.append(username)

        self._execute(query, tuple(values))
        return True  # Пользователь успешно обновлен

    def update_password(self, username: str, new_password_hash: str):
        query = "UPDATE users SET password_hash = %s WHERE username = %s"
        self._execute(query, (new_password_hash, username))

    def add_test(self, test: Test):
        query = "INSERT INTO tests (user_id, type_id, score, difficulty) VALUES (%s, %s, %s, %s);"
        self._execute(query, (test.user_id, test.type_id, test.score, test.difficulty))

    def delete_user(self, user_id: int):
        query = "DELETE FROM users WHERE user_id = %s;"
        self._execute(query, (user_id,))

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