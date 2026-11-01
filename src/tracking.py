"""Journalisation MLflow. Le CI et les tests n'en dependent pas : toute erreur est signalee, pas bloquante."""
import os


def log_run(experiment, run_name, params, metrics, tags=None, artifacts=None):
    try:
        import mlflow
        mlflow.set_tracking_uri(os.environ.get("MLFLOW_TRACKING_URI", "sqlite:///mlflow.db"))
        mlflow.set_experiment(experiment)
        with mlflow.start_run(run_name=run_name):
            mlflow.log_params({k: str(v) for k, v in params.items()})
            mlflow.log_metrics({k: float(v) for k, v in metrics.items()})
            if tags:
                mlflow.set_tags({k: str(v) for k, v in tags.items()})
            for path in artifacts or []:
                mlflow.log_artifact(str(path))
        return True
    except Exception as exc:  # noqa: BLE001  MLflow indisponible : on continue, mais on le dit
        print(f"[tracking] MLflow indisponible, run non journalise : {type(exc).__name__}: {exc}")
        return False
