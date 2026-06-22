package com.nhanes.health_analytics.repository;

import com.nhanes.health_analytics.model.GoldAnalyticsMaster;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

@Repository
public interface GoldAnalyticsRepository extends JpaRepository<GoldAnalyticsMaster, Integer> {
}
