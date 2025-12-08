import os

class ServerConfig:
    def __init__(self):
        self.environment = os.getenv("ENVIRONMENT", "development")
        self.debug = os.getenv("DEBUG", "false").lower() in ("1", "true", "yes")
        self.port = int(os.getenv("PORT", "8000"))

    def to_dict(self):
        return {
            "environment": self.environment,
            "debug": self.debug,
            "port": self.port,
        }
