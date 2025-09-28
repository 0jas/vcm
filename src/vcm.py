from git import Repo
from .exceptions import *
import re, semver, os

class VersionControlManager:
    """A manager class for handling Git tags with semantic versioning.

    This class provides functionality to create, manage, and increment Git tags
    following semantic versioning patterns. It supports development, release candidate,
    patch, and production tags with proper validation and incrementing logic.

    Attributes:
        repo (Repo): The GitPython repository object for the managed repository.
    """
    def __init__(self, repo_path: str):
        """Initialize the VersionControlManager with a repository path.

        If the repository doesn't exist at the given path, it will be created
        and initialized as a new Git repository.

        Args:
            repo_path (str): The file system path to the Git repository.
        """
        if not os.path.isdir(repo_path):
            os.mkdir(repo_path)
            self.repo = Repo.init(repo_path)
        else:
            self.repo = Repo(repo_path)


    @staticmethod
    def get_init_rc_tag(tag: str):
        """Generate an initial release candidate tag from a prerelease tag.

        Takes a prerelease tag (e.g., "1.2.3-dev.4") and converts it to
        an initial release candidate tag (e.g., "1.2.3-rc.1").

        Args:
            tag (str): A prerelease tag in the format "X.Y.Z-prerelease.N"

        Returns:
            str: The corresponding initial RC tag in format "X.Y.Z-rc.1"

        Raises:
            ValueError: If the tag doesn't match the expected prerelease pattern.
        """
        pattern = r"^(\d+)\.(\d+)\.(\d+)-([a-z]+)\.(\d+)$"
        if not re.fullmatch(pattern, tag):
            raise ValueError

        current_tag = semver.VersionInfo.parse(tag)
        return f"{current_tag.major}.{current_tag.minor}.{current_tag.patch}-rc.1"


    def find_tag(self, tag: str):
        """Check if a specific tag exists in the repository.

        Performs an exact match search for the given tag name in the repository's
        tag collection.

        Args:
            tag (str): The exact tag name to search for.

        Returns:
            bool: True if the tag exists, False otherwise.
        """
        pattern = r"^" + tag + r"$"
        return any(re.search(pattern,t.name.strip()) for t in self.repo.tags)


    def find_tag_with_pattern(self, pattern: str):
        """Find the highest semantic version tag matching a regex pattern.

        Searches through all repository tags for those matching the given regex pattern,
        then returns the highest version according to semantic versioning rules.

        Args:
            pattern (str): Regular expression pattern to match against tag names.

        Returns:
            str or None: The highest semantic version tag matching the pattern,
                        or None if no matching tags are found.
        """
        tags = [tag.name.strip() for tag in self.repo.tags if re.search(pattern, tag.name)]
        sorted_tags = sorted(tags, key=semver.VersionInfo.parse, reverse=True)
        return sorted_tags[0] if sorted_tags else None


    def get_current_tag(self, prerelease_tag: str="dev", production: bool= False):
        """Get the current highest tag for a specific type (prerelease or production).

        Retrieves the highest semantic version tag of either production format (X.Y.Z)
        or prerelease format (X.Y.Z-prerelease.N) based on the parameters.

        Args:
            prerelease_tag (str, optional): The prerelease identifier (e.g., "dev", "rc").
                                          Defaults to "dev".
            production (bool, optional): If True, searches for production tags (X.Y.Z format).
                                       If False, searches for prerelease tags. Defaults to False.

        Returns:
            str or None: The highest matching tag, or None if no matching tags exist.
        """
        if production:
            dev_pattern = r"^(\d+)\.(\d+)\.(\d+)$"
        else:
            dev_pattern = r"^(\d+)\.(\d+)\.(\d+)-" + prerelease_tag + r"\.(\d+)$"

        return self.find_tag_with_pattern(dev_pattern)


    def increment_prerelease_tag(self, tag: str=None, prerelease_tag: str="dev", major_bump: bool= False):
        """Create and increment a prerelease tag.

        Creates a new prerelease tag by either incrementing an existing tag or starting
        a new version sequence. Handles major/minor version bumps when transitioning
        from one prerelease to another.

        Args:
            tag (str, optional): Base tag to increment from. If None, starts with "0.1.0-dev.1".
            prerelease_tag (str, optional): The prerelease identifier. Defaults to "dev".
            major_bump (bool, optional): If True, performs a major version bump instead of minor.
                                       Defaults to False.

        Returns:
            str: The newly created prerelease tag.

        Raises:
            ValueError: If the provided tag doesn't match the expected prerelease pattern.
        """
        pattern = r"^(\d+)\.(\d+)\.(\d+)-([a-z]+)\.(\d+)$"
        if tag:
            if not re.fullmatch(pattern,tag):
                raise ValueError
            if self.find_tag(self.get_init_rc_tag(tag)):
                if major_bump:
                    next_tag = f"{semver.VersionInfo.parse(tag).bump_major()}-{prerelease_tag}.1"
                else:
                    next_tag = f"{semver.VersionInfo.parse(tag).bump_minor()}-{prerelease_tag}.1"
            else:
                next_tag = semver.VersionInfo.parse(tag).bump_prerelease()
        else:
            next_tag = f"0.1.0-{prerelease_tag}.1"

        self.repo.create_tag(next_tag)
        return next_tag


    def init_new_rc(self, prerelease_tag: str="dev"):
        """Initialize a new release candidate from the current development tag.

        Creates the first release candidate tag (X.Y.Z-rc.1) based on the highest
        existing development tag. The RC tag points to the same commit as the dev tag.

        Args:
            prerelease_tag (str, optional): The development prerelease identifier.
                                          Defaults to "dev".

        Returns:
            str or None: The newly created RC tag name, or None if no development
                        tag exists to base the RC on.
        """
        current_dev_tag = self.get_current_tag(prerelease_tag)
        if current_dev_tag:
            t = semver.VersionInfo.parse(current_dev_tag)
            init_release_tag = f"{t.major}.{t.minor}.{t.patch}-rc.1"
            self.repo.create_tag(
                init_release_tag,
                ref=self.repo.commit(current_dev_tag),
                message=(
                    f"Release candidate version: {init_release_tag} " 
                    f"created from Development version: {current_dev_tag}"
                )
            )
            return init_release_tag

        return None


    def init_new_patch(self):
        """Initialize a new patch prerelease from the current production tag.

        Creates the first patch prerelease tag (X.Y.Z-patch.1) based on the highest
        existing production tag. The patch tag points to the same commit as the production tag.

        Returns:
            str or None: The newly created patch tag name, or None if no production
                        tag exists to base the patch on.
        """
        current_prod = self.get_current_tag(production=True)
        if current_prod:
            init_patch_tag = f"{current_prod}-patch.1"
            self.repo.create_tag(
                init_patch_tag,
                ref=self.repo.commit(current_prod),
                message=(
                    f"Patch version: {init_patch_tag} " 
                    f"created from Production version: {current_prod}"
                )
            )
            return init_patch_tag

        return None


    def get_current_rc_patch(self, tag: str, prerelease_tag: str="rc"):
        """Get the current highest RC or patch tag for a given base version.

        Finds the highest prerelease tag (rc or patch) that corresponds to the given
        base production version tag.

        Args:
            tag (str): Base production version tag in format "X.Y.Z".
            prerelease_tag (str, optional): The prerelease type ("rc" or "patch").
                                           Defaults to "rc".

        Returns:
            str or None: The highest matching prerelease tag, or None if none exist.

        Raises:
            ValueError: If the base tag doesn't match the production version pattern.
        """
        pattern = r"^(\d+)\.(\d+)\.(\d+)$"
        if not re.fullmatch(pattern, tag):
            raise ValueError

        rc_pattern = r"^" + tag + r"-" + prerelease_tag + r"\.(\d+)$"
        return self.find_tag_with_pattern(rc_pattern)


    def increment_rc_patch(self, tag: str, prerelease_tag: str="rc"):
        """Increment a release candidate or patch prerelease tag.

        Creates the next RC or patch prerelease tag for a given base version.
        Includes validation to ensure proper versioning rules are followed.

        Args:
            tag (str): Base production version tag in format "X.Y.Z".
            prerelease_tag (str, optional): The prerelease type ("rc" or "patch").
                                           Defaults to "rc".

        Returns:
            str or None: The newly created incremented tag, or None if no base
                        prerelease tag exists to increment.

        Raises:
            ValueError: If the base tag doesn't match the production version pattern.
            InvalidTagCreation: If attempting to create an RC when production version
                              exists, or attempting to create a patch when production
                              version doesn't exist, or when a patch already exists
                              in production.
        """
        pattern = r"^(\d+)\.(\d+)\.(\d+)$"
        if not re.fullmatch(pattern, tag):
            raise ValueError

        if  prerelease_tag == "rc" and self.find_tag(tag):
            raise InvalidTagCreation(
                "Production version available. Cannot create Release Candidate version!"
            )
        elif prerelease_tag == "patch" and not self.find_tag(tag):
            raise InvalidTagCreation(
                "Production version not available. Cannot create Patch version!"
            )
        elif prerelease_tag == "rc":
            current_rc = self.get_current_rc_patch(tag)
        elif prerelease_tag == "patch":
            if self.find_tag(str(semver.VersionInfo.parse(tag).bump_patch())):
                raise InvalidTagCreation(
                    "Cannot increment Patch pre-release version. Patch found in Production."
                )
            current_rc = self.get_current_rc_patch(tag, "patch")

        if current_rc:
            new_rc_tag = semver.VersionInfo.parse(current_rc).bump_prerelease()
            self.repo.create_tag(new_rc_tag)
            return new_rc_tag

        return None


    def create_prod_tag(self, tag: str):
        """Create a production tag from a release candidate or patch prerelease.

        Converts an RC or patch prerelease tag into a production version tag.
        For RC tags, creates the base version (X.Y.Z). For patch tags, creates
        the next patch version (X.Y.Z+1).

        Args:
            tag (str): The RC or patch prerelease tag to promote to production.
                      Format: "X.Y.Z-rc.N" or "X.Y.Z-patch.N".

        Returns:
            str: The newly created production tag.

        Raises:
            ValueError: If the tag doesn't match the expected RC or patch pattern.
        """
        pattern = r"^(\d+)\.(\d+)\.(\d+)-(rc|patch)\.(\d+)$"
        if not re.fullmatch(pattern, tag):
            raise ValueError

        if re.match(pattern,tag).group(4) == "patch":
            new_prod_tag = semver.VersionInfo.parse(tag).bump_patch()
        else:
            t = semver.VersionInfo.parse(tag)
            new_prod_tag = f"{t.major}.{t.minor}.{t.patch}"

        self.repo.create_tag(
            new_prod_tag,
            ref=self.repo.commit(tag),
            message=(
                f"Production version: {new_prod_tag} "
                f"created from (Release Candidate | Patch) version: {tag}"
            )
        )
        return new_prod_tag
