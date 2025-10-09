class InvalidTagCreation(Exception):
    """Custom exception raised when attempting to create an invalid Git tag.

    This exception is used to prevent the creation of tags that would violate
    the versioning rules enforced by the VersionControlManager class.
    """
    def __init__(self, message="Do not try to create an INVALID TAG!"):
        self.message = message
        super().__init__(self.message)