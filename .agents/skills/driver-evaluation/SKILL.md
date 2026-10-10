---
name: driver-evaluation
description: Scoring and charting rules for Formula E driver performance analysis.
---

# Driver Evaluation Skill

## Scoring Rules

### Sensor Fault Detection
- If either `turn_3_regen_kw` or `turn_13_regen_kw` exceeds 600 kW, flag `sensor_fault_detected = true`.
- Add a warning feedback string indicating which sensor(s) reported anomalous values.
- Cap the faulty value at 600 kW for all downstream scoring and charting.

### Braking Efficiency (0–50 points)
| Condition | Points |
|-----------|--------|
| Both turns >= 500 kW | 50 |
| Exactly one turn >= 500 kW | 25 |
| Neither turn >= 500 kW | 10 |

### Lift-and-Coast Efficiency (0–50 points)
| Condition | Points |
|-----------|--------|
| Distance >= 50 m | 50 |
| 25 m <= distance < 50 m | 25 |
| Distance < 25 m | 0 |

### Final Score
- `efficiency_score = braking_points + lift_and_coast_points`, clamped to the range [1, 100].

### Rating
| Score Range | Rating |
|-------------|--------|
| >= 85 | EXCELLENT |
| >= 60 | OPTIMAL |
| < 60 | NEEDS_IMPROVEMENT |

### Feedback
- Add specific, actionable feedback for every rule that was not fully met.
- Examples: "Increase Turn 3 regenerative braking above 500 kW for full braking points."

## Charting Rules
- Use `matplotlib.use("Agg")` **before** importing `pyplot`.
- Use a near-black red background theme (`#0a0204`).
- **Left panel**: grouped bar chart for Turn 3 and Turn 13 regen values.
  - Dashed gold line (`#ffd700`) at 500 kW (target threshold).
  - Dashed white line (`#ffffff`) at 600 kW (sensor fault threshold).
  - Bars color: hot accent (`#ff4d5e`).
- **Right panel**: single bar for lift-and-coast distance.
  - Dashed line at 50 m (target).
  - Bar color: primary red (`#ff1e3c`).
- Always close the figure after saving to avoid memory leaks.
