package com.nhanes.health_analytics.controller;

import com.nhanes.health_analytics.model.GoldAnalyticsMaster;
import com.nhanes.health_analytics.repository.GoldAnalyticsRepository;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageRequest;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.CrossOrigin;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/v1/analytics")
public class AnalyticsController {

    private final GoldAnalyticsRepository repository;
    
    @Autowired
    private org.springframework.jdbc.core.JdbcTemplate jdbcTemplate;

    @Autowired
    public AnalyticsController(GoldAnalyticsRepository repository) {
        this.repository = repository;
    }

    @GetMapping
    public ResponseEntity<Page<GoldAnalyticsMaster>> getAnalytics(org.springframework.data.domain.Pageable pageable) {
        // Exponer los datos con paginación y ordenamiento
        Page<GoldAnalyticsMaster> result = repository.findAll(pageable);
        return ResponseEntity.ok(result);
    }

    @CrossOrigin(origins = "*")
    @GetMapping("/member3")
    public ResponseEntity<java.util.List<java.util.Map<String, Object>>> getMember3Data() {
        String sql = "SELECT * FROM public.nhanes_lab_gold LIMIT 150";
        try {
            java.util.List<java.util.Map<String, Object>> data = jdbcTemplate.queryForList(sql);
            return ResponseEntity.ok(data);
        } catch (Exception e) {
            return ResponseEntity.ok(new java.util.ArrayList<>());
        }
    }
}
