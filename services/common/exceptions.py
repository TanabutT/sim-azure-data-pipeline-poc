class ConfigException(Exception):
    """Raised when configuration is missing or invalid"""
    pass


class StorageException(Exception):
    """Raised when storage operations fail"""
    pass


class PipelineException(Exception):
    """Raised when pipeline execution fails"""
    pass


class ActivityException(Exception):
    """Raised when activity execution fails"""
    pass


class SchedulerException(Exception):
    """Raised when scheduler operations fail"""
    pass
