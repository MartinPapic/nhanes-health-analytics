package com.nhanes.health_analytics.repository;

import com.nhanes.health_analytics.model.LongevityMetric;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;

@Repository
public interface LongevityMetricRepository extends JpaRepository<LongevityMetric, Long> {
    
    List<LongevityMetric> findBySurveyCycle(String surveyCycle);
    
    List<LongevityMetric> findByAgeYears(Integer ageYears);
}
