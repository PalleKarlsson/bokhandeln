"""A simple book store application."""
import sys
from datetime import datetime

from decouple import config
import requests
import mariadb
import isbnlib
from PyQt5.QtWidgets import (
    QApplication,
    QDialog,
    QMainWindow,
)
from PyQt5 import QtCore, QtGui
from PyQt5.QtGui import QImage, QPixmap
from main_window import Ui_MainWindow
from dialog import Ui_Dialog


HEADERS = [
    "ISBN",
    "Författare",
    "Titel",
    "Språk",
    "År",
    "Inköpspris",
    "Säljpris",
    "Hylla",
    "Antal i lager",
]

REMOVE_ONE = "UPDATE inventory SET amount = amount - 1 WHERE ISBN = ?"
ADD_ONE = "UPDATE inventory SET amount = amount + 1 WHERE ISBN = ?"
NO_COVER = "no_cover.png"

CONN = None


class Window(QMainWindow, Ui_MainWindow):
    """Main window of the Bokhandeln application."""

    def __init__(self, parent=None):
        """Initialize the main window of the Bokhandeln application."""
        super().__init__(parent)
        self.setupUi(self)
        self.connect_signals_slots()
        model = self.initialize_table()
        self.proxy = QtCore.QSortFilterProxyModel(self)
        self.proxy.setSourceModel(model)
        self.proxy.setFilterKeyColumn(1)
        self.proxy.setFilterCaseSensitivity(QtCore.Qt.CaseInsensitive)
        self.table_inventory.setModel(self.proxy)
        self.line_search.textChanged.connect(self.on_apply_search)
        self.table_inventory.show()

    def on_apply_search(self):
        """Filter the table based on the text entered in the search line edit."""
        self.proxy.setFilterRegExp(self.line_search.text())

    def __populate_table__(self, model, inventory):
        """Populate the table with data from the inventory."""
        for i, (isbn, author, title, lang, year, buy_price, sell_price, row, amount) in enumerate(
            inventory
        ):
            item_isbn = QtGui.QStandardItem(isbn)
            item_author = QtGui.QStandardItem(author)
            item_title = QtGui.QStandardItem(title)
            item_lang = QtGui.QStandardItem(lang)
            item_year = QtGui.QStandardItem(str(year))
            item_buy_price = QtGui.QStandardItem(str(buy_price))
            item_sell_price = QtGui.QStandardItem(str(sell_price))
            item_row = QtGui.QStandardItem(row)
            item_amount = QtGui.QStandardItem(str(amount))
            model.setItem(i, 0, item_isbn)
            model.setItem(i, 1, item_author)
            model.setItem(i, 2, item_title)
            model.setItem(i, 3, item_lang)
            model.setItem(i, 4, item_year)
            model.setItem(i, 5, item_buy_price)
            model.setItem(i, 6, item_sell_price)
            model.setItem(i, 7, item_row)
            model.setItem(i, 8, item_amount)

    def initialize_table(self):
        """Initialize the table with data from the inventory."""
        cursor = CONN.cursor()
        cursor.execute(
            "SELECT ISBN, author, title, lang, year, buy_price, sell_price, row, amount FROM inventory"
        )
        inventory = cursor.fetchall()
        model = QtGui.QStandardItemModel()
        model.setHorizontalHeaderLabels(HEADERS)
        self.__populate_table__(model, inventory)
        return model

    def update_table(self):
        """Update the table with the latest data from the inventory."""
        cursor = CONN.cursor()
        cursor.execute(
            "SELECT ISBN, author, title, lang, year, buy_price, sell_price, row, amount FROM inventory"
        )
        inventory = cursor.fetchall()
        if len(inventory) == 0:
            model = QtGui.QStandardItemModel()
            model.setHorizontalHeaderLabels(HEADERS)
            return model
        model = QtGui.QStandardItemModel()
        model.setHorizontalHeaderLabels(HEADERS)
        self.__populate_table__(model, inventory)
        self.proxy.setSourceModel(model)
        self.table_inventory.show()
        return model

    def connect_signals_slots(self):
        """Connect signals and slots."""
        self.action_open_dialog.triggered.connect(self.open_dialog)
        self.action_add_one.triggered.connect(self.add_one)
        self.action_sell_book.triggered.connect(self.sell_book)
        self.action_delete_book.triggered.connect(self.delete_book)
        self.action_delete_one.triggered.connect(self.delete_one)
        self.action_edit_book.triggered.connect(self.edit_book)
        self.action_toggle.triggered.connect(self.toggle)

    def toggle(self):
        """Set button_sell_book enabled or disabled depending on if a seller is specified."""
        if len(self.line_seller.text()):
            self.button_sell_book.setEnabled(False)
        else:
            self.button_sell_book.setEnabled(True)

    def sell_book(self):
        """Sell the selected book(s) and update the inventory and sales tables."""
        rows = sorted(set(index.row() for index in self.table_inventory.selectedIndexes()))
        cursor = CONN.cursor()
        for row in rows:
            model = self.table_inventory.model()
            isbn = (
                model.sourceModel()
                .item(
                    row,
                )
                .text()
            )
            cursor.execute(
                REMOVE_ONE,
                (isbn,),
            )
            cursor.execute(
                "INSERT INTO sales (ISBN, date, price, seller) VALUES (?,?,?,?)",
                (
                    isbn,
                    datetime.now(),
                    self.line_sell_price.text(),
                    self.line_seller.text(),
                ),
            )
        CONN.commit()
        self.update_table()

    def delete_book(self):
        """Remove the selected book(s) and update the inventory without adding a sales item."""
        rows = sorted(set(index.row() for index in self.table_inventory.selectedIndexes()))
        cursor = CONN.cursor()
        for row in rows:
            model = self.table_inventory.model()
            isbn = (
                model.sourceModel()
                .item(
                    row,
                )
                .text()
            )
            cursor.execute(
                "DELETE FROM inventory WHERE ISBN = ?",
                (isbn,),
            )
        CONN.commit()
        self.update_table()

    def add_one(self):
        """Bump the amount of the selected book(s) by one."""
        rows = sorted(set(index.row() for index in self.table_inventory.selectedIndexes()))
        cursor = CONN.cursor()
        for row in rows:
            model = self.table_inventory.model()
            isbn = (
                model.sourceModel()
                .item(
                    row,
                )
                .text()
            )
            cursor.execute(
                ADD_ONE,
                (isbn,),
            )
        CONN.commit()
        self.update_table()

    def delete_one(self):
        """Decrease the amount of the selected book(s) by one."""
        rows = sorted(set(index.row() for index in self.table_inventory.selectedIndexes()))
        cursor = CONN.cursor()
        for row in rows:
            model = self.table_inventory.model()
            isbn = (
                model.sourceModel()
                .item(
                    row,
                )
                .text()
            )
            cursor.execute(
                REMOVE_ONE,
                (isbn,),
            )
        CONN.commit()
        self.update_table()

    def edit_book(self):
        """Open the dialog to edit the selected book."""
        rows = sorted(set(index.row() for index in self.table_inventory.selectedIndexes()))
        model = self.table_inventory.model()
        isbn = (
            model.sourceModel()
            .item(
                rows[0],
            )
            .text()
        )
        self.dialog = BookDialog(isbn)
        self.dialog.update_table.connect(self.update_table)
        self.dialog.exec()

    def open_dialog(self):
        """Sell the selected book(s) and update the inventory and sales tables."""
        self.dialog = BookDialog(None)
        self.dialog.update_table.connect(self.update_table)
        self.dialog.exec()


class BookDialog(QDialog, Ui_Dialog):
    """Book dialog of the Bokhandeln application."""

    update_table = QtCore.pyqtSignal(bool)

    def __init__(self, isbn, parent=None):
        """Initialize the book dialog of the Bokhandeln application."""
        super().__init__(parent)
        self.setupUi(self)
        self.connect_signals_slots()
        print(isbn)
        if isbn is not None:
            self.line_isbn.setText(isbn)
            self.lookup_book()

    def connect_signals_slots(self):
        """Connect signals and slots."""
        self.action_lookup_book.triggered.connect(self.lookup_book)
        self.action_add_book.triggered.connect(self.add_book)
        self.action_close_dialog.triggered.connect(self.close_dialog)
        self.action_toggle_sale.triggered.connect(self.toggle_sale)

    def close_dialog(self):
        """Close the book dialog."""
        self.done(0)

    def toggle_sale(self):
        """Toggle between saving and selling a book."""
        if self.button_save.text() == "Spara":
            self.button_save.setText("Sälj")
        elif self.button_save.text() == "Sälj":
            self.button_save.setText("Spara")

    def lookup_book(self):
        """Fetch book information from the database or internet and populate the form."""
        cur = CONN.cursor()
        isbn = isbnlib.canonical(self.line_isbn.text())
        cur.execute(
            "SELECT title, author, lang, year, buy_price, sell_price, row, amount, cover FROM inventory WHERE ISBN=?",
            (isbn,),
        )
        result = cur.fetchone()
        if result is not None:
            self.line_title.setText(result[0])
            self.line_author.setText(result[1])
            self.line_language.setText(result[2])
            self.line_year.setText(str(result[3]))
            self.line_buy_price.setText(str(result[4]))
            self.line_sell_price.setText(str(result[5]))
            self.line_row.setText(str(result[6]))
            self.line_amount.setText(str(result[7]))
            if result[8] == NO_COVER:
                self.label_cover.setPixmap(QPixmap(NO_COVER))
                self.label_cover.show()
            else:
                image = QImage()
                image.loadFromData(requests.get(result[8], timeout=5).content)
                self.label_cover.setPixmap(QPixmap(image))
                self.label_cover.show()
        else:
            book_info = isbnlib.meta(isbn)
            self.line_title.setText(book_info["Title"])
            self.line_author.setText(book_info["Authors"][0])
            self.line_year.setText(book_info["Year"])
            self.line_language.setText(book_info["Language"])
            self.line_amount.setText("0")
            if "thumbnail" in isbnlib.cover(isbn):
                image = QImage()
                image.loadFromData(
                    requests.get(isbnlib.cover(isbn)["thumbnail"], timeout=5).content
                )
                self.label_cover.setPixmap(QPixmap(image))
                self.label_cover.show()
            else:
                self.label_cover.setPixmap(QPixmap(NO_COVER))
                self.label_cover.show()

    def __clear_form__(self):
        """Clear all fields in the book dialog form and sets focus to the ISBN field."""
        self.line_isbn.setText("")
        self.line_author.setText("")
        self.line_title.setText("")
        self.line_language.setText("")
        self.line_year.setText("")
        self.line_buy_price.setText("")
        self.line_sell_price.setText("")
        self.line_row.setText("")
        self.line_amount.setText("")
        self.line_isbn.setFocus()
        self.label_cover.setPixmap(QPixmap(NO_COVER))
        self.label_cover.show()

    def add_book(self):
        """Add a book to the inventory."""
        if self.button_save.text() == "Spara":
            cursor = CONN.cursor()
            if "thumbnail" in isbnlib.cover(self.line_isbn.text()):
                cover = isbnlib.cover(self.line_isbn.text())["thumbnail"]
            else:
                cover = NO_COVER
            book = {
                "ISBN": self.line_isbn.text(),
                "author": self.line_author.text(),
                "title": self.line_title.text(),
                "lang": self.line_language.text(),
                "year": self.line_year.text(),
                "buy_price": self.line_buy_price.text(),
                "sell_price": self.line_sell_price.text(),
                "row": self.line_row.text(),
                "cover": cover,
                "amount": 1,
            }
            placeholders = ", ".join(["%s"] * len(book))
            columns = ", ".join(book.keys())
            sql = f"""
                INSERT INTO inventory ({columns}) VALUES ( {placeholders} ) ON DUPLICATE KEY UPDATE
                    author = VALUES(author),
                    title = VALUES(title),
                    lang = VALUES(lang),
                    year = VALUES(year),
                    buy_price = VALUES(buy_price),
                    sell_price = VALUES(sell_price),
                    row = VALUES(row),
                    amount = amount + 1
                """
            cursor.execute(sql, tuple(book.values()))
            CONN.commit()
            if self.line_amount.text() is not None:
                self.line_amount.setText(str(int(self.line_amount.text()) + 1))
            else:
                self.line_amount.setText("1")
            self.update_table.emit(True)
            self.__clear_form__()
        elif self.button_save.text() == "Sälj":
            cursor = CONN.cursor()
            cursor.execute(
                REMOVE_ONE,
                (self.line_isbn.text(),),
            )
            cursor.execute(
                "INSERT INTO sales (ISBN, date, price, seller) VALUES (?,?,?,?)",
                (
                    self.line_isbn.text(),
                    datetime.now(),
                    self.line_sell_price.text(),
                    self.line_seller.text(),
                ),
            )
            CONN.commit()
            self.line_amount.setText(str(int(self.line_amount.text()) - 1))
            self.update_table.emit(True)
            self.__clear_form__()


if __name__ == "__main__":
    BOKHANDELN_DB_USER = config("BOKHANDELN_DB_USER")
    BOKHANDELN_DB_PASSWORD = config("BOKHANDELN_DB_PASSWORD")
    BOKHANDELN_DB_HOST = config("BOKHANDELN_DB_HOST")
    BOKHANDELN_DB_PORT = config("BOKHANDELN_DB_PORT")
    BOKHANDELN_DB_DATABASE = config("BOKHANDELN_DB_DATABASE")
    try:
        CONN = mariadb.connect(
            user=BOKHANDELN_DB_USER,
            password=BOKHANDELN_DB_PASSWORD,
            host=BOKHANDELN_DB_HOST,
            port=int(BOKHANDELN_DB_PORT),
            database=BOKHANDELN_DB_DATABASE,
        )
    except mariadb.Error as e:
        print(f"Error connecting to MariaDB Platform: {e}")
        sys.exit(1)
    app = QApplication(sys.argv)
    win = Window()
    win.show()
    sys.exit(app.exec())
