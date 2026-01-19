package com.mycompany.app;

import java.time.OffsetDateTime;

public class JobPosting {

    private final String id;
    private final String title;
    private final String company;
    private final String location;
    private final String url;
    private final OffsetDateTime createdAt;

    public JobPosting(String id, String title, String company, String location, String url, OffsetDateTime createdAt) {
        this.id = id;
        this.title = title;
        this.company = company;
        this.location = location;
        this.url = url;
        this.createdAt = createdAt;
    }

    public String getId() {
        return id;
    }

    public String getTitle() {
        return title;
    }

    public String getCompany() {
        return company;
    }

    public String getLocation() {
        return location;
    }

    public String getUrl() {
        return url;
    }

    public OffsetDateTime getCreatedAt() {
        return createdAt;
    }
}
