# app/services/metrics.py
import numpy as np

class GlucoseMetricsCalculator:
    TARGET_RANGE_LOW = 3.9
    TARGET_RANGE_HIGH = 10.0
    SEVERE_HYPO = 3.0
    SEVERE_HYPER = 13.9

    @staticmethod
    def calculate_daily_metrics(readings: list[float]) -> dict[str, float]:
        if len(readings) < 10:
            raise ValueError("Se requieren al menos 10 lecturas para calcular métricas")

        readings_array = np.array(readings)

        mean_glucose = float(np.mean(readings_array))
        std_glucose = float(np.std(readings_array))
        min_glucose = float(np.min(readings_array))
        max_glucose = float(np.max(readings_array))
        median_glucose = float(np.median(readings_array))
        cv = (std_glucose / mean_glucose * 100) if mean_glucose > 0 else 0
        tir = float(np.sum((readings_array >= GlucoseMetricsCalculator.TARGET_RANGE_LOW) &
                          (readings_array <= GlucoseMetricsCalculator.TARGET_RANGE_HIGH)) / len(readings_array) * 100)
        tbr = float(np.sum(readings_array < GlucoseMetricsCalculator.TARGET_RANGE_LOW) / len(readings_array) * 100)
        tbr_severe = float(np.sum(readings_array < GlucoseMetricsCalculator.SEVERE_HYPO) / len(readings_array) * 100)
        tar = float(np.sum(readings_array > GlucoseMetricsCalculator.TARGET_RANGE_HIGH) / len(readings_array) * 100)
        tar_severe = float(np.sum(readings_array > GlucoseMetricsCalculator.SEVERE_HYPER) / len(readings_array) * 100)
        mean_glucose_mgdl = mean_glucose * 18.0182
        gmi = 3.31 + (0.02392 * mean_glucose_mgdl)
        glucose_range = max_glucose - min_glucose

        return {
            'mean_glucose': round(mean_glucose, 2),
            'median_glucose': round(median_glucose, 2),
            'std_glucose': round(std_glucose, 2),
            'min_glucose': round(min_glucose, 2),
            'max_glucose': round(max_glucose, 2),
            'glucose_range': round(glucose_range, 2),
            'cv': round(cv, 2),
            'tir': round(tir, 2),
            'tbr': round(tbr, 2),
            'tbr_severe': round(tbr_severe, 2),
            'tar': round(tar, 2),
            'tar_severe': round(tar_severe, 2),
            'gmi': round(gmi, 2),
            'n_readings': len(readings)
        }