import sys
from datetime import datetime


import requests
import mariadb
from PyQt5.QtWidgets import (
    QApplication,
    QDialog,
    QMainWindow,
    QTableWidget,
    QTableWidgetItem,
    QLineEdit,
)
from PyQt5 import QtCore, QtGui
from main_window import Ui_MainWindow
from dialog import Ui_Dialog
from PyQt5.QtGui import QImage, QPixmap
import isbnlib


class Window(QMainWindow, Ui_MainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)
        self.connectSignalsSlots()
        model = self.update_table()
        self.proxy = QtCore.QSortFilterProxyModel(self)
        self.proxy.setSourceModel(model)
        self.proxy.setFilterKeyColumn(1)
        self.proxy.setFilterCaseSensitivity(QtCore.Qt.CaseInsensitive)
        self.table_inventory.setModel(self.proxy)
        self.line_search.textChanged.connect(self.on_apply_search)
        self.table_inventory.show()

    def on_apply_search(self):
        self.proxy.setFilterRegExp(self.line_search.text())

    def update_table(self):
        cursor = conn.cursor()
        cursor.execute(
            "SELECT ISBN, author, title, lang, year, buy_price, sell_price, row, amount FROM inventory"
        )
        inventory = cursor.fetchall()
        model = QtGui.QStandardItemModel()
        model.setHorizontalHeaderLabels(
            [
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
        )
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
            # self.table_inventory.show()

        return model

    def connectSignalsSlots(self):
        self.action_open_dialog.triggered.connect(self.open_dialog)
        self.action_sell_book.triggered.connect(self.sell_book)
        self.action_delete_book.triggered.connect(self.delete_book)
        self.action_edit_book.triggered.connect(self.edit_book)
        self.action_search.triggered.connect(self.search)

    def sell_book(self):
        pass

    def delete_book(self):
        pass

    def edit_book(self):
        pass

    def open_dialog(self):
        dialog = BookDialog(self)
        dialog.update_table.connect(self.update_table)
        dialog.exec()

    def confirm_add(self):
        pass

    def search(self):
        pass


class BookDialog(QDialog, Ui_Dialog):
    update_table = QtCore.pyqtSignal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)
        self.connectSignalsSlots()

    def connectSignalsSlots(self):
        self.action_lookup_book.triggered.connect(self.lookup_book)
        self.action_add_book.triggered.connect(self.add_book)
        self.action_close_dialog.triggered.connect(self.close_dialog)
        self.action_toggle_sale.triggered.connect(self.toggle_sale)

    def close_dialog(self):
        pass

    def toggle_sale(self):
        if self.button_save.text() == "Spara":
            self.button_save.setText("Sälj")
        elif self.button_save.text() == "Sälj":
            self.button_save.setText("Spara")
        pass

    def lookup_book(self):
        cur = conn.cursor()
        isbn = isbnlib.canonical(self.line_isbn.text())
        cur.execute("SELECT * FROM inventory WHERE ISBN=?", (isbn,))
        result = cur.fetchone()
        print(result)
        if result is not None:
            self.line_title.setText(result[1])
            self.line_author.setText(result[2])
            self.line_language.setText(result[3])
            self.line_year.setText(str(result[4]))
            self.line_buy_price.setText(str(result[5]))
            self.line_sell_price.setText(str(result[6]))
            self.line_row.setText(str(result[7]))
            self.line_amount.setText(str(result[9]))
            if result[8] == "no_cover.png":
                image = QImage()
                self.label_cover.setPixmap(QPixmap("no_cover.png"))
                self.label_cover.show()
            else:
                image = QImage()
                image.loadFromData(requests.get(result[8]).content)
                self.label_cover.setPixmap(QPixmap(image))
                self.label_cover.show()
        else:
            book_info = isbnlib.meta(isbn)
            print(book_info)
            self.line_title.setText(book_info["Title"])
            self.line_author.setText(book_info["Authors"][0])
            self.line_year.setText(book_info["Year"])
            self.line_language.setText(book_info["Language"])
            self.line_amount.setText("0")
            if "thumbnail" in isbnlib.cover(isbn):
                image = QImage()
                image.loadFromData(requests.get(isbnlib.cover(isbn)["thumbnail"]).content)
                self.label_cover.setPixmap(QPixmap(image))
                self.label_cover.show()
            else:
                image = QImage()
                self.label_cover.setPixmap(QPixmap("no_cover.png"))
                self.label_cover.show()

    def clear_form(self):
        self.line_isbn.setText("")
        self.line_author.setText("")
        self.line_title.setText("")
        self.line_language.setText("")
        self.line_year.setText("")
        self.line_buy_price.setText("")
        self.line_sell_price.setText("")
        self.line_row.setText("")
        self.line_amount.setText("")

    def add_book(self):
        if self.button_save.text() == "Spara":
            cursor = conn.cursor()
            if "thumbnail" in isbnlib.cover(self.line_isbn.text()):
                cover = isbnlib.cover(self.line_isbn.text())["thumbnail"]
            else:
                cover = "no_cover.png"
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
            sql = (
                "INSERT INTO %s ( %s ) VALUES ( %s ) ON DUPLICATE KEY UPDATE author = VALUES(author), title = VALUES(title), lang = VALUES(lang), year = VALUES(year), buy_price = VALUES(buy_price), sell_price = VALUES(sell_price), row = VALUES(row), amount = amount + 1"
                % (
                    "inventory",
                    columns,
                    placeholders,
                )
            )
            print(sql)
            cursor.execute(sql, list(book.values()))
            conn.commit()
            self.line_amount.setText(str(int(self.line_amount.text()) + 1))
            self.update_table.emit(True)
            self.clear_form()
        elif self.button_save.text() == "Sälj":
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE inventory SET amount = amount -1 WHERE ISBN = ?",
                (self.line_isbn.text(),),
            )
            cursor.execute(
                "INSERT INTO sales VALUES (?,?,?,?)",
                (
                    self.line_isbn.text(),
                    datetime.now(),
                    self.line_sell_price.text(),
                    self.line_seller.text(),
                ),
            )
            conn.commit()
            self.line_amount.setText(str(int(self.line_amount.text()) - 1))
            self.update_table.emit(True)
            self.clear_form()


if __name__ == "__main__":
    try:
        conn = mariadb.connect(
            user="bokhandeln",
            password="421frölunda",
            host="localhost",
            port=3306,
            database="bokhandeln",
        )
    except mariadb.Error as e:
        print(f"Error connecting to MariaDB Platform: {e}")
        sys.exit(1)
    app = QApplication(sys.argv)
    win = Window()
    win.show()
    sys.exit(app.exec())
