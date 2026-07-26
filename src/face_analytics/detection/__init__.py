"""Replaceable in-memory face detection interfaces and implementations."""

from face_analytics.detection.base import BoundingBox, Detection, FaceDetector
from face_analytics.detection.mediapipe_detector import (
    MediaPipeDetector,
    MediaPipeUnavailableError,
)
from face_analytics.detection.opencv_detector import OpenCVHaarDetector

__all__ = [
    "BoundingBox",
    "Detection",
    "FaceDetector",
    "MediaPipeDetector",
    "MediaPipeUnavailableError",
    "OpenCVHaarDetector",
]
