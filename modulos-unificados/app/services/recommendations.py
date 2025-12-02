# app/services/recommendations.py
from typing import List, Optional, Dict, Any
from app.models.schemas import Recommendation, RecommendationLevel

class RecommendationEngine:
    @staticmethod
    def generate_recommendations(
        cluster_info: Dict[str, Any],
        current_metrics: Dict[str, float],
        historical_trend: Optional[str] = None
    ) -> List[Recommendation]:
        recommendations = []
        cluster_id = cluster_info['cluster_id']
        cluster_name = cluster_info['cluster_name']
        tir = current_metrics.get('tir', 0)
        cv = current_metrics.get('cv', 0)
        tbr = current_metrics.get('tbr', 0)
        tar = current_metrics.get('tar', 0)
        gmi = current_metrics.get('gmi', 0)

        if current_metrics.get('tbr_severe', 0) > 1:
            recommendations.append(Recommendation(
                level=RecommendationLevel.CRITICAL,
                category="Hipoglucemia",
                title="Riesgo de Hipoglucemia Severa Detectado",
                description="Se ha detectado hipoglucemia severa (<3.0 mmol/L). Contacte inmediatamente a su médico para ajustar dosis de insulina basal.",
                priority=1
            ))

        if tbr > 4:
            recommendations.append(Recommendation(
                level=RecommendationLevel.HIGH,
                category="Hipoglucemia",
                title="Tiempo en Hipoglucemia Elevado",
                description=f"Su TBR es {tbr:.1f}% (objetivo: <4%). Considere reducir la dosis de insulina basal y revisar el factor de sensibilidad a la insulina.",
                priority=2
            ))

        if tar > 25:
            recommendations.append(Recommendation(
                level=RecommendationLevel.HIGH,
                category="Hiperglucemia",
                title="Tiempo en Hiperglucemia Frecuente",
                description=f"Su TAR es {tar:.1f}% (objetivo: <25%). Revise el conteo de carbohidratos y considere ajustar el ratio de insulina a carbohidratos.",
                priority=3
            ))

        if cv > 36:
            recommendations.append(Recommendation(
                level=RecommendationLevel.MODERATE,
                category="Variabilidad",
                title="Alta Variabilidad Glucémica",
                description=f"Su CV es {cv:.1f}% (objetivo: <36%). La alta variabilidad aumenta el riesgo de complicaciones. Considere mejorar el conteo de carbohidratos y la consistencia en horarios de comidas.",
                priority=4
            ))

        if tir < 70:
            recommendations.append(Recommendation(
                level=RecommendationLevel.MODERATE,
                category="Control General",
                title="Tiempo en Rango Subóptimo",
                description=f"Su TIR es {tir:.1f}% (objetivo: >70%). Trabaje con su equipo médico para optimizar su tratamiento.",
                priority=5
            ))

        if gmi > 7.0:
            recommendations.append(Recommendation(
                level=RecommendationLevel.MODERATE,
                category="HbA1c",
                title="GMI Elevado",
                description=f"Su GMI estimado es {gmi:.1f}% (objetivo: <7.0%). Esto sugiere un control glucémico que podría mejorarse.",
                priority=6
            ))

        cluster_specific = RecommendationEngine._get_cluster_specific_recommendations(cluster_id, cluster_name)
        recommendations.extend(cluster_specific)

        if historical_trend == "worsening":
            recommendations.append(Recommendation(
                level=RecommendationLevel.HIGH,
                category="Tendencia",
                title="Control Glucémico en Deterioro",
                description="Se ha detectado una tendencia de empeoramiento en su control glucémico. Programe una cita con su médico para revisar el tratamiento.",
                priority=2
            ))
        elif historical_trend == "improving":
            recommendations.append(Recommendation(
                level=RecommendationLevel.INFO,
                category="Tendencia",
                title="Mejora en Control Glucémico",
                description="¡Excelente trabajo! Su control glucémico está mejorando. Continue con sus hábitos actuales.",
                priority=10
            ))

        if tir > 70 and cv < 36 and tbr < 4 and tar < 25:
            recommendations.append(Recommendation(
                level=RecommendationLevel.INFO,
                category="Control General",
                title="Excelente Control Glucémico",
                description="Su control glucémico está dentro de los objetivos. ¡Siga así!",
                priority=11
            ))

        recommendations.sort(key=lambda x: x.priority)
        return recommendations

    @staticmethod
    def _get_cluster_specific_recommendations(cluster_id: int, cluster_name: str) -> List[Recommendation]:
        cluster_recommendations = {
            0: [Recommendation(
                level=RecommendationLevel.INFO,
                category="Cluster",
                title="Perfil: Control Excelente",
                description="Usted pertenece al grupo de pacientes con mejor control glucémico. Mantenga sus hábitos actuales.",
                priority=12
            )],
            1: [Recommendation(
                level=RecommendationLevel.MODERATE,
                category="Cluster",
                title="Perfil: Control Moderado",
                description="Su control es bueno pero tiene margen de mejora. Enfóquese en optimizar el conteo de carbohidratos y el timing de insulina.",
                priority=7
            )],
            2: [Recommendation(
                level=RecommendationLevel.HIGH,
                category="Cluster",
                title="Perfil: Alta Variabilidad",
                description="Usted pertenece al grupo con alta variabilidad glucémica. Considere tecnología de lazo cerrado (bomba + CGM) y educación en conteo avanzado de carbohidratos.",
                priority=3
            )],
            3: [Recommendation(
                level=RecommendationLevel.HIGH,
                category="Cluster",
                title="Perfil: Riesgo de Hipoglucemia",
                description="Usted pertenece al grupo con mayor riesgo de hipoglucemia. Es prioritario revisar las dosis de insulina basal con su médico.",
                priority=2
            )],
            4: [Recommendation(
                level=RecommendationLevel.HIGH,
                category="Cluster",
                title="Perfil: Control Subóptimo",
                description="Su control glucémico requiere optimización. Programe una cita con su equipo médico para revisar completamente el tratamiento.",
                priority=3
            )]
        }
        return cluster_recommendations.get(cluster_id, [])