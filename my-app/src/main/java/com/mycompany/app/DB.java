package com.mycompany.app;

import java.sql.Connection;
import java.sql.DriverManager;
import java.sql.SQLException;

public class DB {

    private static String setting(String name, String fallback) {
        String value = System.getenv(name);
        return value == null || value.isBlank() ? fallback : value;
    }

    private static final String URL
            = "jdbc:mysql://" + setting("DB_HOST", "localhost")
            + ":" + setting("DB_PORT", "3306")
            + "/" + setting("DB_NAME", "jobmarket_db");

    private static final String USER = setting("DB_USER", "root");
    private static final String PASSWORD = setting("DB_PASSWORD", "");

    public static Connection getConnection() throws SQLException {
        return DriverManager.getConnection(URL, USER, PASSWORD);
    }
}
