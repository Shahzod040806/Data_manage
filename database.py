import sqlite3
from datetime import date
import json

# Подключение к базе данных
conn = sqlite3.connect('orders.db')
cursor = conn.cursor()


def create_tables():
    # Выполнение SQL-запросов для создания таблиц
    cursor.executescript('''
        CREATE TABLE IF NOT EXISTS Clients (
            client_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            order_number TEXT UNIQUE,
            order_date DATE
        );

        CREATE TABLE IF NOT EXISTS Products (
            product_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            quantity INT DEFAULT 0 CHECK (quantity >= 0),
            price REAL CHECK (price > 0)
        );

        CREATE TABLE IF NOT EXISTS Orders (
            order_id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id INT,
            total_price REAL CHECK (total_price > 0),
            FOREIGN KEY (client_id) REFERENCES Clients(client_id) ON DELETE CASCADE
        );
    ''')


def add_client(name, order_number):
    try:
        cursor.execute("INSERT INTO Clients (name, order_number, order_date) VALUES (?, ?, ?)",
                       (name, order_number, date.today()))
        conn.commit()
        print(f"Клиент {name} успешно добавлен.")
    except sqlite3.IntegrityError as e:
        if str(e).startswith('UNIQUE constraint failed'):
            print(f"Ошибка: Клиент с таким номером заказа уже существует.")
        else:
            print(f"Произошла ошибка при добавлении клиента: {e}")


def add_product(name, quantity, price):
    try:
        cursor.execute("INSERT INTO Products (name, quantity, price) VALUES (?, ?, ?)", (name, quantity, price))
        conn.commit()
        print(f"Товар '{name}' успешно добавлен.")
    except sqlite3.Error as e:
        print(f"Произошла ошибка при добавлении товара: {e}")


def add_order(client_id, products):
    # Проверяем, существует ли клиент
    cursor.execute("SELECT * FROM Clients WHERE client_id=?", (client_id,))
    client = cursor.fetchone()
    if not client:
        print(f"Клиента с ID {client_id} не существует.")
        return

    # Получаем информацию о продуктах
    total_price = 0
    for product in products:
        product_id, quantity = product
        cursor.execute("SELECT * FROM Products WHERE product_id=? AND quantity>=?", (product_id, quantity))
        product_info = cursor.fetchone()
        if not product_info:
            print(f"Недостаточно товара с ID {product_id} на складе.")
            return
        total_price += product_info['price'] * quantity

    # Проверка на большую сумму
    if total_price > 10000:
        print(f"Внимание! Сумма заказа составляет {total_price}, что превышает 10 000 единиц.")

    # Обновляем количество товаров на складе
    for product in products:
        product_id, quantity = product
        cursor.execute("UPDATE Products SET quantity=quantity-? WHERE product_id=?", (quantity, product_id))

    # Добавляем заказ
    cursor.execute("INSERT INTO Orders (client_id, total_price) VALUES (?, ?)", (client_id, total_price))
    conn.commit()
    print("Заказ успешно создан.")


def execute_order(order_id):
    # Проверяем, существует ли заказ
    cursor.execute("SELECT * FROM Orders WHERE order_id=?", (order_id,))
    order = cursor.fetchone()
    if not order:
        print(f"Заказа с ID {order_id} не существует.")
        return

    # Сохраняем данные о заказе в JSON
    data = {
        "order_id": order["order_id"],
        "client_id": order["client_id"],
        "total_price": order["total_price"]
    }
    with open(f"executed_orders/{order_id}.json", "w") as f:
        json.dump(data, f)

    # Удаляем заказ из таблицы
    cursor.execute("DELETE FROM Orders WHERE order_id=?", (order_id,))
    conn.commit()
    print(f"Заказ с ID {order_id} выполнен и сохранен в файл.")


def menu():
    while True:
        print("\nМеню:")
        print("1. Добавить клиента")
        print("2. Добавить товар")
        print("3. Добавить заказ")
        print("4. Выполнить заказ")
        print("5. Выход")

        choice = input("Выберите действие: ")

        if choice == '1':
            name = input("Введите имя клиента: ")
            order_number = input("Введите номер заказа: ")
            add_client(name, order_number)
        elif choice == '2':
            name = input("Введите наименование товара: ")
            quantity = int(input("Введите количество товара: "))
            price = float(input("Введите цену товара: "))
            add_product(name, quantity, price)
        elif choice == '3':
            client_id = int(input("Введите ID клиента: "))
            products = []
            n = int(input("Сколько товаров в заказе? "))
            for _ in range(n):
                product_id = int(input("Введите ID товара: "))
                quantity = int(input("Введите количество товара: "))
                products.append((product_id, quantity))
            add_order(client_id, products)
        elif choice == '4':
            order_id = int(input("Введите ID заказа: "))
            execute_order(order_id)
        elif choice == '5':
            break
        else:
            print("Неверный выбор. Попробуйте снова.")


if __name__ == "__main__":
    create_tables()  # Создаем таблицы, если их еще нет
    menu()  # Запускаем меню