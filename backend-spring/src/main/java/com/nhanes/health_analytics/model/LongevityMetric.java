package com.nhanes.health_analytics.model;

import jakarta.persistence.*;

@Entity
@Table(name = "longevity_metric")
public class LongevityMetric {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(nullable = false, unique = true)
    private Long seqn; // NHANES respondent sequence number

    @Column(name = "survey_cycle", nullable = false)
    private String surveyCycle; // e.g., "2017-2018"

    @Column(name = "age_years")
    private Integer ageYears;

    private String gender;

    @Column(name = "longevity_group")
    private String longevityGroup;

    @Column(name = "healthy_aging_score")
    private Double healthyAgingScore;

    public LongevityMetric() {}

    // Getters and Setters
    public Long getId() { return id; }
    public void setId(Long id) { this.id = id; }

    public Long getSeqn() { return seqn; }
    public void setSeqn(Long seqn) { this.seqn = seqn; }

    public String getSurveyCycle() { return surveyCycle; }
    public void setSurveyCycle(String surveyCycle) { this.surveyCycle = surveyCycle; }

    public Integer getAgeYears() { return ageYears; }
    public void setAgeYears(Integer ageYears) { this.ageYears = ageYears; }

    public String getGender() { return gender; }
    public void setGender(String gender) { this.gender = gender; }

    public String getLongevityGroup() { return longevityGroup; }
    public void setLongevityGroup(String longevityGroup) { this.longevityGroup = longevityGroup; }

    public Double getHealthyAgingScore() { return healthyAgingScore; }
    public void setHealthyAgingScore(Double healthyAgingScore) { this.healthyAgingScore = healthyAgingScore; }
}
