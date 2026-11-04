"""Eight-state constant-velocity filter; dt and velocity use the same time unit.
Timestamp-aware callers use seconds and pixels/second. Legacy callers use dt=1.
Q is the exact discretization of independent white acceleration processes.
"""
import numpy as np


class KalmanFilter:
    def __init__(self, std_pos=4.0, std_size=6.0, std_vel=8.0, std_acc=2.0):
        self.dim_x, self.dim_z = 8, 4
        self.F = np.eye(8)
        self.H = np.zeros((4, 8)); self.H[:, :4] = np.eye(4)
        self.R = np.diag([std_pos**2]*2 + [std_size**2]*2).astype(float)
        self.acceleration_variance = np.array([std_vel**2]*2 + [(std_vel*.5)**2]*2)
        self.Q = np.zeros((8, 8))
        self.x = np.zeros((8, 1)); self.P = np.eye(8)*10
        self.P[4:, 4:] = np.eye(4)*200

    def initialize(self, measurement, velocity_scale=1.0):
        z = np.asarray(measurement, dtype=float).reshape(4)
        if not np.isfinite(z).all(): raise ValueError("Nonfinite measurement")
        self.x = np.zeros((8, 1)); self.x[:4, 0] = z
        self.P = np.zeros((8, 8)); self.P[:4, :4] = self.measurement_noise(z)
        self.P[4:, 4:] = np.eye(4)*200*velocity_scale**2
        self._valid_size()

    def measurement_noise(self, z):
        # Larger boxes exhibit larger detector boundary jitter. Same R for gate/update.
        z = np.asarray(z).reshape(4)
        return np.diag(np.maximum(np.diag(self.R),
            np.array([.05*z[2], .05*z[3], .10*z[2], .10*z[3]])**2))

    def predict(self, dt=1.0):
        if not np.isfinite(dt) or dt < 0: raise ValueError("dt must be finite and nonnegative")
        self.F = np.eye(8); self.F[:4, 4:] = np.eye(4)*dt
        q = np.diag(self.acceleration_variance)
        self.Q = np.block([[q*dt**3/3, q*dt**2/2], [q*dt**2/2, q*dt]])
        self.x = self.F @ self.x
        self.P = self.F @ self.P @ self.F.T + self.Q
        self.P = (self.P+self.P.T)*.5
        self._valid_size()
        return self.x

    def innovation(self, measurement, confidence=1.0, measurement_mask=None):
        z=np.asarray(measurement,dtype=float).reshape(4,1)
        noise=self.measurement_noise(z)/max(.2,min(1.,float(confidence)))
        mask=np.ones(4,dtype=bool) if measurement_mask is None else np.asarray(measurement_mask,dtype=bool)
        h=self.H[mask];noise=noise[np.ix_(mask,mask)]
        residual=z[mask]-h@self.x
        covariance=h@self.P@h.T+noise
        return residual,covariance,noise

    def update(self, measurement, confidence=1.0, measurement_mask=None):
        residual, covariance, noise=self.innovation(measurement,confidence,measurement_mask)
        mask=np.ones(4,dtype=bool) if measurement_mask is None else np.asarray(measurement_mask,dtype=bool)
        h=self.H[mask]
        gain=np.linalg.solve(covariance, h@self.P).T
        self.x += gain@residual
        a=np.eye(8)-gain@h
        self.P=a@self.P@a.T+gain@noise@gain.T  # Joseph form
        self.P=(self.P+self.P.T)*.5
        self._valid_size()
        return self.x

    def _valid_size(self):
        for i in [2,3]:
            if self.x[i,0] < 1:
                self.x[i,0]=1
                if self.x[i+4,0] < 0: self.x[i+4,0]=0

    @property
    def state(self): return self.x.flatten().copy()
    @property
    def centroid(self): return tuple(float(v) for v in self.x[:2,0])
    @property
    def size(self): return tuple(max(1.,float(v)) for v in self.x[2:4,0])
    @property
    def velocity(self): return tuple(float(v) for v in self.x[4:6,0])
