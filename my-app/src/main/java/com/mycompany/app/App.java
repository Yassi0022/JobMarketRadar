package com.mycompany.app;

import java.io.Reader;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.sql.Connection;
import java.sql.Date;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.sql.Types;
import java.time.OffsetDateTime;
import java.util.Arrays;

import com.opencsv.CSVReader;
import com.opencsv.CSVReaderBuilder;

public class App {

    public static void main(String[] args) {
        // Repo root (JobMarketRadar) -> my-app -> src/main/python
        Path repoDir = Paths.get(System.getProperty("user.dir"));
        Path projectDir = repoDir.resolve("my-app");
        Path pyDir = projectDir.resolve("src").resolve("main").resolve("python");

        // Python venv inside src/main/python/.venv
        String pythonExe = pyDir.resolve(".venv").resolve("Scripts").resolve("python.exe").toString();

        Path ingestPy = pyDir.resolve("adzuna_ingest.py");
        Path reportPy = pyDir.resolve("market_report.py");
        Path csvFile = pyDir.resolve("jobs.csv");

        // MySQL UPSERT (one ON DUPLICATE KEY UPDATE only)
        String upsertSql
                = "INSERT INTO job_postings "
                + "(source, adzuna_id, title, company, location, url, posted_at) "
                + "VALUES (?, ?, ?, ?, ?, ?, ?) AS new_data "
                + "ON DUPLICATE KEY UPDATE "
                + "source    = new_data.source, "
                + "adzuna_id = new_data.adzuna_id, "
                + "title     = new_data.title, "
                + "company   = new_data.company, "
                + "location  = new_data.location, "
                + "url       = new_data.url, "
                + "posted_at = new_data.posted_at";

        int invalid = 0;
        int invalidDate = 0;

        try {
            // 1) Python ingest -> jobs.csv
            int c1 = run(pyDir, pythonExe, ingestPy.toString());
            if (c1 != 0) {
                throw new RuntimeException("adzuna_ingest.py failed, exitCode=" + c1);
            }

            if (!Files.exists(csvFile)) {
                throw new RuntimeException("CSV not found: " + csvFile);
            }

            // 2) Java import CSV -> DB
            try (Connection conn = DB.getConnection(); PreparedStatement ps = conn.prepareStatement(upsertSql)) {

                conn.setAutoCommit(false);

                try (Reader reader = Files.newBufferedReader(csvFile); CSVReader csv = new CSVReaderBuilder(reader).withSkipLines(1).build()) {

                    String[] parts;
                    int row = 0;

                    int batchSize = 500;
                    int batchCount = 0;

                    while ((parts = csv.readNext()) != null) {
                        if (row < 5) {
                            System.out.println("ROW " + row + " " + Arrays.toString(parts));
                        }
                        row++;

                        if (parts.length < 6) {
                            invalid++;
                            continue;
                        }

                        // CSV: query,id,title,company,location,created,redirect_url
                        String source = "adzuna_it";
                        String adzunaIdRaw = safe(parts[0]);
                        String title = safe(parts[1]);
                        String company = safe(parts[2]);
                        String location = safe(parts[3]);
                        String createdRaw = safe(parts[4]);
                        String url = safe(parts[5]);

                        if (adzunaIdRaw.isEmpty() || title.isEmpty() || location.isEmpty() || url.isEmpty()) {
                            invalid++;
                            continue;
                        }

                        long adzunaId;
                        try {
                            adzunaId = Long.parseLong(adzunaIdRaw);
                        } catch (Exception ex) {
                            invalid++;
                            continue;
                        }

                        Date postedAt = null;
                        if (!createdRaw.isEmpty()) {
                            try {
                                postedAt = Date.valueOf(OffsetDateTime.parse(createdRaw).toLocalDate());
                            } catch (Exception ex) {
                                invalidDate++;
                                postedAt = null;
                            }
                        }

                        ps.setString(1, source);
                        ps.setLong(2, adzunaId);
                        ps.setString(3, title);
                        ps.setString(4, company);
                        ps.setString(5, location);
                        ps.setString(6, url);

                        if (postedAt == null) {
                            ps.setNull(7, Types.DATE);
                        } else {
                            ps.setDate(7, postedAt);
                        }

                        ps.addBatch();
                        batchCount++;

                        if (batchCount % batchSize == 0) {
                            ps.executeBatch();
                        }
                    }

                    ps.executeBatch();
                    conn.commit();
                }
            }

            // 3) Python report 
            int c3 = run(pyDir, pythonExe, reportPy.toString());
            if (c3 != 0) {
                throw new RuntimeException("market_report.py failed, exitCode=" + c3);
            }

            System.out.println("Done. Invalid rows: " + invalid);
            System.out.println("Rows with invalid dates: " + invalidDate);

        } catch (Exception e) {
            e.printStackTrace();
            System.out.println("If you see SQL errors, check DB name/table and DB password in DB.java");
            System.exit(1);
        }
    }

    private static String safe(String s) {
        return s == null ? "" : s.trim();
    }

    private static int countRows(Connection conn) throws SQLException {
        try (PreparedStatement ps = conn.prepareStatement("SELECT COUNT(*) FROM job_postings"); ResultSet rs = ps.executeQuery()) {
            rs.next();
            return rs.getInt(1);
        }
    }

    static int run(Path workDir, String... cmd) throws Exception {
        ProcessBuilder pb = new ProcessBuilder(cmd);
        pb.directory(workDir.toFile());
        pb.inheritIO();
        Process p = pb.start();
        return p.waitFor();
    }
}
