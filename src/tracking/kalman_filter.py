"""
Kalman Filter for object tracking
Using constant velocity motion model
"""

import numpy as np
from filterpy.kalman import KalmanFilter as FilterPyKalmanFilter
from filterpy.common import Q_discrete_white_noise


class KalmanFilter:
    """
    Kalman Filter for bounding box tracking

    State vector: [x, y, a, h, vx, vy, va, vh]
    where:
        x, y: center position
        a: aspect ratio (width/height)
        h: height
        vx, vy, va, vh: velocities
    """

    def __init__(self):
        """Initialize Kalman filter"""
        # State dimension: 8 (x, y, a, h, vx, vy, va, vh)
        # Measurement dimension: 4 (x, y, a, h)
        self.kf = FilterPyKalmanFilter(dim_x=8, dim_z=4)

        # State transition matrix (constant velocity model)
        dt = 1.0
        self.kf.F = np.array([
            [1, 0, 0, 0, dt, 0, 0, 0],   # x = x + vx*dt
            [0, 1, 0, 0, 0, dt, 0, 0],   # y = y + vy*dt
            [0, 0, 1, 0, 0, 0, dt, 0],   # a = a + va*dt
            [0, 0, 0, 1, 0, 0, 0, dt],   # h = h + vh*dt
            [0, 0, 0, 0, 1, 0, 0, 0],    # vx = vx
            [0, 0, 0, 0, 0, 1, 0, 0],    # vy = vy
            [0, 0, 0, 0, 0, 0, 1, 0],    # va = va
            [0, 0, 0, 0, 0, 0, 0, 1]     # vh = vh
        ])

        # Measurement function (we only observe position and size)
        self.kf.H = np.array([
            [1, 0, 0, 0, 0, 0, 0, 0],    # measure x
            [0, 1, 0, 0, 0, 0, 0, 0],    # measure y
            [0, 0, 1, 0, 0, 0, 0, 0],    # measure a
            [0, 0, 0, 1, 0, 0, 0, 0]     # measure h
        ])

        # Measurement uncertainty
        self.kf.R *= 1.0

        # Process uncertainty
        self.kf.Q[-1, -1] *= 0.01
        self.kf.Q[4:, 4:] *= 0.01

        # Initial state uncertainty
        self.kf.P[4:, 4:] *= 1000.0  # High uncertainty for velocities
        self.kf.P *= 10.0

        self.std_weight_position = 1.0 / 20
        self.std_weight_velocity = 1.0 / 160

    def initiate(self, measurement: np.ndarray) -> tuple:
        """
        Initialize state with first measurement

        Args:
            measurement: [x, y, a, h]

        Returns:
            mean: Initial state mean
            covariance: Initial state covariance
        """
        mean = np.zeros(8)
        mean[:4] = measurement

        std = [
            2 * self.std_weight_position * measurement[3],  # x std
            2 * self.std_weight_position * measurement[3],  # y std
            1e-2,                                           # a std
            2 * self.std_weight_position * measurement[3],  # h std
            10 * self.std_weight_velocity * measurement[3], # vx std
            10 * self.std_weight_velocity * measurement[3], # vy std
            1e-5,                                           # va std
            10 * self.std_weight_velocity * measurement[3]  # vh std
        ]

        covariance = np.diag(np.square(std))

        return mean, covariance

    def predict(self, mean: np.ndarray, covariance: np.ndarray) -> tuple:
        """
        Predict next state

        Args:
            mean: Current state mean
            covariance: Current state covariance

        Returns:
            mean: Predicted state mean
            covariance: Predicted state covariance
        """
        std = [
            self.std_weight_position * mean[3],
            self.std_weight_position * mean[3],
            1e-2,
            self.std_weight_position * mean[3],
            self.std_weight_velocity * mean[3],
            self.std_weight_velocity * mean[3],
            1e-5,
            self.std_weight_velocity * mean[3]
        ]

        motion_cov = np.diag(np.square(std))

        mean = np.dot(self.kf.F, mean)
        covariance = np.linalg.multi_dot((self.kf.F, covariance, self.kf.F.T)) + motion_cov

        return mean, covariance

    def update(self, mean: np.ndarray, covariance: np.ndarray, measurement: np.ndarray) -> tuple:
        """
        Update state with new measurement

        Args:
            mean: Predicted state mean
            covariance: Predicted state covariance
            measurement: New measurement [x, y, a, h]

        Returns:
            mean: Updated state mean
            covariance: Updated state covariance
        """
        std = [
            self.std_weight_position * mean[3],
            self.std_weight_position * mean[3],
            1e-1,
            self.std_weight_position * mean[3]
        ]

        innovation_cov = np.diag(np.square(std))

        # Compute Kalman gain
        projected_mean = np.dot(self.kf.H, mean)
        projected_cov = np.linalg.multi_dot((
            self.kf.H, covariance, self.kf.H.T
        )) + innovation_cov

        kalman_gain = np.linalg.multi_dot((
            covariance, self.kf.H.T, np.linalg.inv(projected_cov)
        ))

        # Update state
        innovation = measurement - projected_mean
        new_mean = mean + np.dot(kalman_gain, innovation)
        new_covariance = covariance - np.linalg.multi_dot((
            kalman_gain, self.kf.H, covariance
        ))

        return new_mean, new_covariance
