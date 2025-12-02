# app/services/clustering.py
import joblib
import numpy as np
import os

class ClusteringService:
    def __init__(self, model_path: str = "d:/Taller1/glucose_kmeans_model.pkl"):
        self.model_path = model_path
        self.kmeans_model = None
        self.scaler = None
        self.feature_names = [
            'avg_mean_glucose',
            'avg_cv',
            'avg_tir',
            'avg_tbr',
            'avg_tar',
            'avg_gmi'
        ]
        self.cluster_names = {
            0: "Control Excelente",
            1: "Control Moderado",
            2: "Alta Variabilidad",
            3: "Riesgo Hipoglucemia",
            4: "Control Subóptimo"
        }
        self.load_model()

    def load_model(self):
        try:
            if os.path.exists(self.model_path):
                model_data = joblib.load(self.model_path)
                self.kmeans_model = model_data['kmeans']
                self.scaler = model_data['scaler']
                self.cluster_names = model_data.get('cluster_names', self.cluster_names)
                print(f"✅ Modelo cargado desde {self.model_path}")
            else:
                print(f"⚠️ Modelo no encontrado en {self.model_path}. Se usará clustering en tiempo real.")
        except Exception as e:
            print(f"❌ Error cargando modelo: {e}")

    def assign_cluster(self, patient_metrics: dict[str, float]) -> dict[str, any]:
        if self.kmeans_model is None:
            raise ValueError("Modelo no disponible. Entrena el modelo primero.")

        features = np.array([[
            patient_metrics.get('avg_mean_glucose', 0),
            patient_metrics.get('avg_cv', 0),
            patient_metrics.get('avg_tir', 0),
            patient_metrics.get('avg_tbr', 0),
            patient_metrics.get('avg_tar', 0),
            patient_metrics.get('avg_gmi', 0)
        ]])

        if self.scaler:
            features_scaled = self.scaler.transform(features)
        else:
            features_scaled = features

        cluster_id = int(self.kmeans_model.predict(features_scaled)[0])
        distances = self.kmeans_model.transform(features_scaled)[0]
        confidence = float(1.0 / (1.0 + distances[cluster_id]))

        return {
            'cluster_id': cluster_id,
            'cluster_name': self.cluster_names.get(cluster_id, f"Cluster {cluster_id}"),
            'confidence_score': round(confidence, 3),
            'distances_to_all_clusters': distances.tolist()
        }