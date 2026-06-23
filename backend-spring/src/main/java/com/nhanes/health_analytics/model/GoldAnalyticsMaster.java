package com.nhanes.health_analytics.model;

import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import jakarta.persistence.Table;

@Entity
@Table(name = "gold_analytics_master")
public class GoldAnalyticsMaster {

    @Id
    private Integer seqn;
    
    private String surveyCycle;
    private Integer ageYears;
    private String gender;
    private String longevityGroup;
    private Double healthyAgingScore;

    public GoldAnalyticsMaster() {}

    public Integer getSeqn() {
        return seqn;
    }

    public void setSeqn(Integer seqn) {
        this.seqn = seqn;
    }

    public String getSurveyCycle() {
        return surveyCycle;
    }

    public void setSurveyCycle(String surveyCycle) {
        this.surveyCycle = surveyCycle;
    }

    public Integer getAgeYears() {
        return ageYears;
    }

    public void setAgeYears(Integer ageYears) {
        this.ageYears = ageYears;
    }

    public String getGender() {
        return gender;
    }

    public void setGender(String gender) {
        this.gender = gender;
    }

    public String getLongevityGroup() {
        return longevityGroup;
    }

    public void setLongevityGroup(String longevityGroup) {
        this.longevityGroup = longevityGroup;
    }

    public Double getHealthyAgingScore() {
        return healthyAgingScore;
    }

    public void setHealthyAgingScore(Double healthyAgingScore) {
        this.healthyAgingScore = healthyAgingScore;
    }
}
