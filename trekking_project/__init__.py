import pymysql

pymysql.version_info = (1, 4, 3, "final", 0) # Fake phiên bản để tránh lỗi tương thích
pymysql.install_as_MySQLdb()