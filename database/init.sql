CREATE TABLE IF NOT EXISTS users (
    user_id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    first_name VARCHAR(50),
    last_name VARCHAR(50),
    email VARCHAR(100) UNIQUE NOT NULL,
    phone_number VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    role VARCHAR(20) DEFAULT 'user'
);

CREATE TABLE IF NOT EXISTS test_categories (
    category_id SERIAL PRIMARY KEY,
    category_name VARCHAR(100) UNIQUE NOT NULL
);

CREATE TABLE IF NOT EXISTS test_types (
    type_id SERIAL PRIMARY KEY,
    type_name VARCHAR(100) UNIQUE NOT NULL,
    category_id INT REFERENCES test_categories(category_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS tests (
    test_id SERIAL PRIMARY KEY,
    user_id INT REFERENCES users(user_id) ON DELETE CASCADE,
    type_id INT REFERENCES test_types(type_id) ON DELETE CASCADE,
    score INT CHECK (score BETWEEN 1 AND 100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    difficulty VARCHAR(20)
);

--CREATE TABLE IF NOT EXISTS confirmation_tokens (
--    id SERIAL PRIMARY KEY,
--    username VARCHAR(255) NOT NULL,
--    token VARCHAR(255) NOT NULL,
--    updated_data JSONB NOT NULL,
--    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
--    expires_at TIMESTAMP
--);