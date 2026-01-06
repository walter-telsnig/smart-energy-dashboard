from locust import HttpUser, task, between
import random

class SmartEnergyUser(HttpUser):
    # approximate wait time between tasks (simulating user think time)
    wait_time = between(1, 3)

    @task(1)
    def health_check(self):
        """Lightweight check to ensure API is up."""
        self.client.get("/health", name="/health")

    @task(2)
    def get_pv_catalog(self):
        """Fetch the list of available PV datasets."""
        self.client.get("/api/v1/pv/catalog", name="/api/v1/pv/catalog")

    @task(3)
    def get_pv_sample(self):
        """
        Request a specific PV series. 
        Using a known key like 'pv_2025_hourly' which likely exists.
        """
        # fetching the head (first 48 rows)
        self.client.get("/api/v1/pv/head?key=pv_2025_hourly&n=48", name="/api/v1/pv/head")
        
        # fetching a full series (heavier load)
        self.client.get("/api/v1/pv?key=pv_2025_hourly&limit=100", name="/api/v1/pv (full)")

    def on_start(self):
        """Called when a User starts."""
        # You could perform login here if auth was required
        pass
