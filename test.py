# pip install mysql-connector-python
# pip install pymysql
# pip install sqlalchemy
# pip install python-dotenv
# pip install pickle-mixin
# pip install tabulate


# book.py

from typing import Optional, Dict, Any
from .library_item import LibraryItem

class Book(LibraryItem):
    def __init__(self, id_: Optional[int], title: str, author: str, year: int, price: float):
        self._id = id_
        self._title = title
        self._author = author
        self._year = int(year)
        self._price = float(price)

    @property
    def id(self): return self._id
    @id.setter
    def id(self, v): self._id = v

    @property
    def title(self): return self._title
    @title.setter
    def title(self, v): self._title = v

    @property
    def author(self): return self._author
    @author.setter
    def author(self, v): self._author = v

    @property
    def year(self): return self._year
    @year.setter
    def year(self, v): self._year = int(v)

    @property
    def price(self): return self._price
    @price.setter
    def price(self, v): self._price = float(v)

    def display_info(self) -> str:
        return f"[Book] ID={self.id} | {self.title} — {self.author} ({self.year}) — ${self.price:.2f}"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": "book",
            "id": self.id,
            "title": self.title,
            "author": self.author,
            "year": self.year,
            "price": self.price
        }

    @staticmethod
    def from_dict(d: Dict[str, Any]) -> "Book":
        return Book(d.get("id"), d["title"], d["author"], int(d["year"]), float(d["price"]))


class EBook(Book):
    def __init__(self, id_: Optional[int], title: str, author: str, year: int, price: float, file_size: float):
        super().__init__(id_, title, author, year, price)
        self._file_size = float(file_size)

    @property
    def file_size(self): return self._file_size
    @file_size.setter
    def file_size(self, v): self._file_size = float(v)

    def display_info(self) -> None:
        print(f"[EBook] ID={self.id} | {self.title} — {self.author} "
              f"({self.year}) — ${self.price:.2f} — {self.file_size}MB")


# library_item.py 
from abc import ABC, abstractmethod

class LibraryItem(ABC):
    @abstractmethod
    def display_info(self) -> str:
        ...

# db_handler.py

import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, Column, Integer, String, Float, Numeric
from sqlalchemy.orm import sessionmaker, declarative_base
from typing import List
from models.book import Book, EBook

load_dotenv()

DB_URL = os.getenv("DB_URL", "mysql+pymysql://root:password@localhost:3306/library_db")
Base = declarative_base()

class BookModel(Base):
    __tablename__ = "books"
    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(255))
    author = Column(String(255))
    year = Column(Integer)
    price = Column(Numeric(10,2))
    type = Column(String(50))
    file_size = Column(Float, nullable=True)

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "author": self.author,
            "year": self.year,
            "price": float(self.price) if self.price is not None else None,
            "type": self.type,
            "file_size": self.file_size
        }

class DBHandler:
    def __init__(self, db_url: str = DB_URL):
        self.engine = create_engine(db_url, echo=False, future=True)
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)

    def save_books(self, items: List[Book]):
        session = self.Session()
        try:
            for b in items:
                model = BookModel(
                    title=b.title,
                    author=b.author,
                    year=b.year,
                    price=round(b.price,2),
                    type="ebook" if isinstance(b, EBook) else "book",
                    file_size=b.file_size if isinstance(b, EBook) else None
                )
                session.add(model)
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def load_books(self) -> List[Book]:
        session = self.Session()
        try:
            rows = session.query(BookModel).all()
            out = []
            for r in rows:
                data = r.to_dict()
                if data.get("type") == "ebook":
                    out.append(EBook(data["id"], data["title"], data["author"], data["year"], data["price"], data.get("file_size") or 0))
                else:
                    out.append(Book(data["id"], data["title"], data["author"], data["year"], data["price"]))
            return out
        finally:
            session.close()


# file_handler.py

import json
from typing import List
from models.book import Book, EBook
from models.library_item import LibraryItem

def save_to_json(filename: str, items: List[LibraryItem]) -> None:
    arr = [i.to_dict() for i in items]
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(arr, f, ensure_ascii=False, indent=2)

def load_from_json(filename: str) -> List[LibraryItem]:
    try:
        with open(filename, "r", encoding="utf-8") as f:
            arr = json.load(f)
    except FileNotFoundError:
        return []
    loaded = []
    for d in arr:
        if d.get("type") == "ebook":
            loaded.append(EBook.from_dict(d))
        else:
            loaded.append(Book.from_dict(d))
    return loaded



# main.py

import sys
from models.book import Book, EBook
from utils.file_handler import save_to_json, load_from_json
from utils.db_handler import DBHandler  
from typing import List
from tabulate import tabulate


def input_int(prompt, min_val=None, max_val=None):
    while True:
        s = input(prompt).strip()
        try:
            v = int(s)
            if min_val is not None and v < min_val:
                print(f"Phải >= {min_val}")
                continue
            if max_val is not None and v > max_val:
                print(f"Phải <= {max_val}")
                continue
            return v
        except ValueError:
            print("Nhập số nguyên hợp lệ.")


def input_float(prompt, min_val=None):
    while True:
        s = input(prompt).strip()
        try:
            v = float(s)
            if min_val is not None and v < min_val:
                print(f"Phải >= {min_val}")
                continue
            return v
        except ValueError:
            print("Nhập số thực hợp lệ.")


def input_nonempty(prompt):
    while True:
        s = input(prompt).strip()
        if s == "":
            print("Không được để trống.")
        else:
            return s


class Manager:
    def __init__(self):
        self.books: List[Book] = []
        # Tạm thời không dùng DB
        self.db = None

    def _next_id(self):
        ids = [b.id for b in self.books if b.id is not None]
        return max(ids)+1 if ids else 1

    def add_book(self):
        print("1) Sách giấy  2) EBook")
        typ = ""
        while typ not in ("1", "2"):
            typ = input("Chọn: ").strip()
        title = input_nonempty("Tiêu đề: ")
        author = input_nonempty("Tác giả: ")
        year = input_int("Năm: ")
        price = input_float("Giá: ", min_val=0)
        id_ = self._next_id()
        if typ == "1":
            b = Book(id_, title, author, year, price)
        else:
            fs = input_float("Dung lượng (MB): ", min_val=0)
            b = EBook(id_, title, author, year, price, fs)
        self.books.append(b)
        print("Đã thêm:", b.display_info())

    def list_books(self):
        if not self.books:
            print("Danh sách rỗng.")
            return
        for b in self.books:
            print(b.display_info())

    def search(self):
        print("1) Title 2) Author 3) Year")
        c = input("Chọn: ").strip()
        if c == "1":
            q = input_nonempty("Nhập (hoặc 1 phần): ").lower()
            res = [b for b in self.books if q in b.title.lower()]
        elif c == "2":
            q = input_nonempty("Nhập (hoặc 1 phần): ").lower()
            res = [b for b in self.books if q in b.author.lower()]
        elif c == "3":
            y = input_int("Năm: ")
            res = [b for b in self.books if b.year == y]
        else:
            print("Sai.")
            return
        if not res:
            print("Không tìm thấy.")
            return
        for r in res:
            print(r.display_info())

    def update(self):
        id_ = input_int("ID cần cập nhật: ")
        found = next((b for b in self.books if b.id == id_), None)
        if not found:
            print("Không thấy.")
            return
        print("Bỏ trống giữ nguyên.")
        t = input("Tiêu đề mới: ").strip()
        a = input("Tác giả mới: ").strip()
        y = input("Năm mới: ").strip()
        p = input("Giá mới: ").strip()
        if t:
            found.title = t
        if a:
            found.author = a
        if y:
            try:
                found.year = int(y)
            except:
                print("Năm sai, bỏ qua.")
        if p:
            try:
                found.price = float(p)
            except:
                print("Giá sai, bỏ qua.")
        if isinstance(found, EBook):
            fs = input("Dung lượng mới: ").strip()
            if fs:
                try:
                    found.file_size = float(fs)
                except:
                    print("Sai, bỏ qua.")
        print("Đã cập nhật:", found.display_info())

    def delete(self):
        id_ = input_int("ID xóa: ")
        for i, b in enumerate(self.books):
            if b.id == id_:
                ok = input("Xác nhận (y/n): ").strip().lower()
                if ok == "y":
                    self.books.pop(i)
                    print("Đã xóa.")
                else:
                    print("Hủy.")
                return
        print("Không tìm thấy.")

    def save_file(self):
        save_to_json("books.json", self.books)
        print("Đã lưu file books.json")

    def load_file(self):
        self.books = load_from_json("books.json")
        print(f"Đã nạp {len(self.books)} bản ghi từ books.json")

    def save_db(self):
        if not self.db:
            print("DB chưa sẵn sàng")
            return
        self.db.save_books(self.books)
        print("Đã lưu DB")

    def load_db(self):
        if not self.db:
            print("DB chưa sẵn sàng")
            return
        self.books = self.db.load_books()
        print(f"Đã nạp {len(self.books)} bản ghi từ DB")

    def apply_discount(self):
        p = input_float("Phần trăm giảm giá: ", min_val=0)
        for b in self.books:
            old = b.price
            b.price = round(b.price * (1 - p / 100), 2)
            print(f"{b.title}: {old} -> {b.price}")


def show_menu():
    menu_items = [
        ["1", "Thêm sách"],
        ["2", "Hiển thị"],
        ["3", "Tìm kiếm"],
        ["4", "Cập nhật"],
        ["5", "Xóa"],
        ["6", "Lưu file"],
        ["7", "Đọc file"],
        ["8", "Lưu DB"],
        ["9", "Đọc DB"],
        ["10", "Giảm giá"],
        ["0", "Thoát"],
    ]
    print(tabulate(menu_items, headers=["MÃ", "CHỨC NĂNG"], tablefmt="fancy_grid"))


def main():
    m = Manager()
    while True:
        print("\n" + "=" * 40)
        show_menu()
        ch = input("Chọn: ").strip()
        if ch == "1":
            m.add_book()
        elif ch == "2":
            m.list_books()
        elif ch == "3":
            m.search()
        elif ch == "4":
            m.update()
        elif ch == "5":
            m.delete()
        elif ch == "6":
            m.save_file()
        elif ch == "7":
            m.load_file()
        elif ch == "8":
            m.save_db()
        elif ch == "9":
            m.load_db()
        elif ch == "10":
            m.apply_discount()
        elif ch == "0":
            print("Bye")
            sys.exit(0)
        else:
            print("Lựa chọn không hợp lệ.")


if __name__ == "__main__":
    main()



