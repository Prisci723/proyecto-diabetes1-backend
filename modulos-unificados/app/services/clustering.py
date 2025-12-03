# app/services/clustering.py
"""
Servicio de clustering para asignación de pacientes a grupos de control glucémico
"""

import joblib
import numpy as np
import os
import logging
from pathlib import Path
from typing import Dict, Any

logger = logging.getLogger(__name__)


class ClusteringService:
    """Servicio de clustering para clasificar pacientes según su control glucémico"""
    
    def __init__(self, model_path: str = None):
        """
        Inicializa el servicio de clustering
        
        Args:
            model_path: Ruta al archivo del modelo. Si es None, busca en ubicaciones estándar
        """
        # Rutas posibles del modelo
        if model_path:
            self.possible_paths = [Path(model_path)]
        else:
            self.possible_paths = [
                Path("d:/Taller1/glucose_kmeans_model.pkl"),
                Path("/home/priscila/Datos/Documentos Universidad/Ingeniería en Ciencias de la Computación/8 Octavo semestre/SHC134 Taller De Especialidad/proyecto_modulos/glucose_kmeans_model.pkl"),
                Path(__file__).parent.parent / "models" / "glucose_kmeans_model.pkl",
                Path("glucose_kmeans_model.pkl"),
            ]
        
        self.model_path = None
        self.kmeans_model = None
        self.scaler = None
        
        # Nombres de features esperadas
        self.feature_names = [
            'avg_mean_glucose',
            'avg_cv',
            'avg_tir',
            'avg_tbr',
            'avg_tar',
            'avg_gmi'
        ]
        
        # Nombres de clusters (definidos según análisis previo)
        self.cluster_names = {
            0: "Control Excelente",
            1: "Control Moderado",
            2: "Alta Variabilidad",
            3: "Riesgo Hipoglucemia",
            4: "Control Subóptimo"
        }
        
        # Intentar cargar el modelo
        self.load_model()
    
    def load_model(self):
        """
        Carga el modelo pre-entrenado de clustering
        
        Busca en múltiples ubicaciones posibles y carga el primero que encuentre
        """
        try:
            # Buscar modelo en ubicaciones posibles
            for path in self.possible_paths:
                if path.exists():
                    self.model_path = path
                    logger.info(f"📊 Modelo encontrado en: {path}")
                    break
            
            if self.model_path is None:
                logger.warning(
                    f"⚠️  Modelo de clustering no encontrado en las rutas esperadas. "
                    f"Se usará asignación heurística basada en reglas."
                )
                return
            
            # Cargar modelo
            model_data = joblib.load(self.model_path)
            self.kmeans_model = model_data.get('kmeans')
            self.scaler = model_data.get('scaler')
            self.cluster_names = model_data.get('cluster_names', self.cluster_names)
            
            logger.info(f"✅ Modelo de clustering cargado exitosamente")
            logger.info(f"   Clusters disponibles: {len(self.cluster_names)}")
            
        except Exception as e:
            logger.error(f"❌ Error al cargar modelo de clustering: {e}")
            logger.warning("⚠️  Se usará asignación heurística basada en reglas")
            self.kmeans_model = None
    
    def assign_cluster(self, patient_metrics: Dict[str, float]) -> Dict[str, Any]:
        """
        Asigna un paciente a un cluster basado en sus métricas glucémicas
        
        Args:
            patient_metrics: Diccionario con métricas del paciente:
                - avg_mean_glucose: Glucosa promedio
                - avg_cv: Coeficiente de variación
                - avg_tir: Tiempo en rango
                - avg_tbr: Tiempo bajo rango
                - avg_tar: Tiempo sobre rango
                - avg_gmi: Indicador de manejo glucémico
        
        Returns:
            Diccionario con:
                - cluster_id: ID del cluster asignado
                - cluster_name: Nombre descriptivo del cluster
                - confidence_score: Score de confianza (0-1)
                - distances_to_all_clusters: Distancias a todos los centroides
        
        Raises:
            ValueError: Si el modelo no está disponible y no se puede usar heurística
        """
        # Si no hay modelo, usar asignación heurística
        if self.kmeans_model is None:
            return self._assign_cluster_heuristic(patient_metrics)
        
        try:
            # Crear array de features en el orden correcto
            features = np.array([[
                patient_metrics.get('avg_mean_glucose', 0),
                patient_metrics.get('avg_cv', 0),
                patient_metrics.get('avg_tir', 0),
                patient_metrics.get('avg_tbr', 0),
                patient_metrics.get('avg_tar', 0),
                patient_metrics.get('avg_gmi', 0)
            ]])
            
            # Normalizar si hay scaler
            if self.scaler:
                features_scaled = self.scaler.transform(features)
            else:
                features_scaled = features
            
            # Predecir cluster
            cluster_id = int(self.kmeans_model.predict(features_scaled)[0])
            
            # Calcular distancia a centroides (para confidence score)
            distances = self.kmeans_model.transform(features_scaled)[0]
            confidence = float(1.0 / (1.0 + distances[cluster_id]))
            
            return {
                'cluster_id': cluster_id,
                'cluster_name': self.cluster_names.get(cluster_id, f"Cluster {cluster_id}"),
                'confidence_score': round(confidence, 3),
                'distances_to_all_clusters': distances.tolist()
            }
            
        except Exception as e:
            logger.error(f"❌ Error en asignación de cluster: {e}")
            logger.warning("⚠️  Usando asignación heurística como fallback")
            return self._assign_cluster_heuristic(patient_metrics)
    
    def _assign_cluster_heuristic(self, patient_metrics: Dict[str, float]) -> Dict[str, Any]:
        """
        Asigna cluster usando reglas heurísticas cuando no hay modelo
        
        Reglas basadas en estándares clínicos:
        - Control Excelente: TIR >70%, CV <36%, TBR <4%
        - Riesgo Hipoglucemia: TBR >4%
        - Alta Variabilidad: CV >40%
        - Control Subóptimo: TIR <50%
        - Control Moderado: Todo lo demás
        
        Args:
            patient_metrics: Métricas del paciente
            
        Returns:
            Diccionario con información del cluster
        """
        tir = patient_metrics.get('avg_tir', 0)
        cv = patient_metrics.get('avg_cv', 0)
        tbr = patient_metrics.get('avg_tbr', 0)
        tar = patient_metrics.get('avg_tar', 0)
        
        # Reglas de clasificación
        if tir > 70 and cv < 36 and tbr < 4:
            cluster_id = 0  # Control Excelente
            confidence = 0.85
        elif tbr > 4:
            cluster_id = 3  # Riesgo Hipoglucemia
            confidence = 0.80
        elif cv > 40:
            cluster_id = 2  # Alta Variabilidad
            confidence = 0.75
        elif tir < 50:
            cluster_id = 4  # Control Subóptimo
            confidence = 0.80
        else:
            cluster_id = 1  # Control Moderado
            confidence = 0.70
        
        logger.info(f"Asignación heurística: Cluster {cluster_id} ({self.cluster_names[cluster_id]})")
        
        return {
            'cluster_id': cluster_id,
            'cluster_name': self.cluster_names.get(cluster_id, f"Cluster {cluster_id}"),
            'confidence_score': confidence,
            'distances_to_all_clusters': [0.0] * len(self.cluster_names)
        }
    
    def get_cluster_characteristics(self, cluster_id: int) -> Dict[str, Any]:
        """
        Obtiene las características típicas de un cluster
        
        Args:
            cluster_id: ID del cluster
            
        Returns:
            Diccionario con características del cluster
        """
        characteristics = {
            0: {
                "name": "Control Excelente",
                "typical_tir": ">70%",
                "typical_cv": "<36%",
                "typical_tbr": "<4%",
                "risk_level": "Bajo",
                "description": "Pacientes con control glucémico óptimo"
            },
            1: {
                "name": "Control Moderado",
                "typical_tir": "50-70%",
                "typical_cv": "36-40%",
                "typical_tbr": "<4%",
                "risk_level": "Moderado",
                "description": "Pacientes con buen control pero espacio de mejora"
            },
            2: {
                "name": "Alta Variabilidad",
                "typical_tir": "Variable",
                "typical_cv": ">40%",
                "typical_tbr": "Variable",
                "risk_level": "Alto",
                "description": "Pacientes con fluctuaciones glucémicas significativas"
            },
            3: {
                "name": "Riesgo Hipoglucemia",
                "typical_tir": "Variable",
                "typical_cv": "Variable",
                "typical_tbr": ">4%",
                "risk_level": "Alto",
                "description": "Pacientes con episodios frecuentes de hipoglucemia"
            },
            4: {
                "name": "Control Subóptimo",
                "typical_tir": "<50%",
                "typical_cv": "Variable",
                "typical_tbr": "Variable",
                "risk_level": "Muy Alto",
                "description": "Pacientes que requieren optimización urgente"
            }
        }
        
        return characteristics.get(cluster_id, {
            "name": f"Cluster {cluster_id}",
            "description": "Sin información disponible"
        })
    
    def is_model_loaded(self) -> bool:
        """Verifica si el modelo está cargado"""
        return self.kmeans_model is not None