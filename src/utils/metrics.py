"""Evaluation metrics utilities for classification models.

Provides helper functions to compute accuracy, precision, recall, F1, and
produce a classification report using scikit-learn.
"""
from __future__ import annotations
from typing import Dict, List, Any

import numpy as np
from sklearn.metrics import accuracy_score, precision_recall_fscore_support, classification_report, confusion_matrix


def compute_metrics(y_true: np.ndarray, y_pred: np.ndarray, labels: List[str]) -> Dict[str, Any]:
    """Compute common classification metrics.

    Returns a dictionary with accuracy, weighted precision/recall/f1 and a
    text classification report. Confusion matrix is returned as a 2D list.
    """
    acc = accuracy_score(y_true, y_pred)
    precision, recall, f1, _ = precision_recall_fscore_support(
        y_true, y_pred, average="weighted", zero_division=0
    )
    report = classification_report(y_true, y_pred, target_names=labels, zero_division=0)
    cm = confusion_matrix(y_true, y_pred).tolist()
    return {
        "accuracy": float(acc),
        "precision_weighted": float(precision),
        "recall_weighted": float(recall),
        "f1_weighted": float(f1),
        "classification_report": report,
        "confusion_matrix": cm,
    }
