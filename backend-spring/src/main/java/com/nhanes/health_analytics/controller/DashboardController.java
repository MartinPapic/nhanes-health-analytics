package com.nhanes.health_analytics.controller;

import com.nhanes.health_analytics.model.LongevityMetric;
import com.nhanes.health_analytics.repository.LongevityMetricRepository;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Map;
import java.util.HashMap;

@RestController
@RequestMapping("/api/v1/metrics")
@Tag(name = "Dashboard", description = "Endpoints for NHANES Longevity Dashboard")
public class DashboardController {

    @Autowired
    private LongevityMetricRepository repository;

    @GetMapping("/all")
    @Operation(summary = "Get all longevity metrics")
    public List<LongevityMetric> getAllMetrics() {
        return repository.findAll();
    }

    @GetMapping("/summary")
    @Operation(summary = "Get high-level summary KPIs")
    public ResponseEntity<Map<String, Object>> getSummary() {
        long totalSample = repository.count();
        
        Map<String, Object> summary = new HashMap<>();
        summary.put("totalSample", totalSample);
        summary.put("averageLongevityScore", 7.5); // Placeholder, would be calculated from DB
        summary.put("metabolicHealthPercentage", 65.2); // Placeholder
        
        return ResponseEntity.ok(summary);
    }
}
