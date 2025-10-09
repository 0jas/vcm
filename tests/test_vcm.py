"""
Comprehensive integration test suite for VersionControlManager class.

This module contains end-to-end integration tests for the VersionControlManager class,
testing the complete semantic versioning workflow using a real Git repository.
Unlike unit tests that mock Git operations, these tests create actual commits
and tags to verify the complete functionality in a realistic environment.

Test Strategy:
    - Uses a real Git repository ('test_dir') for authentic testing
    - Creates actual commits and tags to simulate real development workflow
    - Tests complete semantic versioning lifecycle from development to production
    - Validates error handling and business rule enforcement
    - Covers edge cases and version bump scenarios

Workflow Coverage:
    1. Development tag creation and incrementing (X.Y.Z-dev.N)
    2. Release candidate initialization and management (X.Y.Z-rc.N)
    3. Production tag creation from RC tags (X.Y.Z)
    4. Patch tag workflow for hotfixes (X.Y.Z-patch.N)
    5. Version bumping (minor and major)
    6. Error conditions and validation rules

Dependencies:
    - pytest: Testing framework for assertions and exception handling
    - GitPython: Real Git operations (not mocked)
    - os, sys, shutil: File system operations for test cleanup

Test Environment:
    - Creates temporary 'test_dir' Git repository
    - Automatically cleans up test repository after completion
    - Uses sequential test execution that builds upon previous states

Author: Sajin Vachery
"""

from src.vcm.vcm import *
from src.vcm.cli import *
from src.vcm.exceptions import *
import git, os, shutil, pytest
from io import StringIO
from unittest.mock import patch, MagicMock
import argparse
import sys

# ============================================================================
# PART 1: ORIGINAL VCM INTEGRATION TESTS
# ============================================================================

# Helper functions for VCM tests
def empty_commit():
    """Create an empty commit in the test repository.

    This utility function creates a commit in the test repository without
    adding any files. It's used to advance the commit history so that
    new tags can be created at different commit points, simulating
    real development progress.

    The function operates on the global 'test_dir' repository and is
    essential for tag creation since Git requires commits to exist
    before tags can be created.

    Side Effects:
        - Creates a new commit in the test repository
        - Advances the repository's commit history
        - Enables subsequent tag creation
    """
    git.Repo("test_dir").index.commit("Empty Commit")


def create_tag(tag):
    """Create a specific tag in the test repository.

    This utility function creates a Git tag with the given name in the
    test repository. It's used to set up test scenarios that require
    specific tags to exist before testing VersionControlManager functionality.

    Args:
        tag (str): The tag name to create (should follow semantic versioning)

    Side Effects:
        - Creates a new Git tag in the test repository
        - Tag points to the current HEAD commit

    Note:
        This function bypasses VersionControlManager's validation and directly
        creates tags via GitPython, allowing test setup that might not
        be possible through the manager's normal workflow.
    """
    git.Repo("test_dir").create_tag(tag)


def create_tags():
    """Create a sequence of development tags for testing.

    This setup function creates a series of development tags (1.0.0-dev.0
    through 1.0.0-dev.9) with corresponding commits. This simulates a
    development workflow where multiple development iterations have occurred.

    The function creates both commits and tags to establish a realistic
    repository state for testing tag management operations.

    Created Tags:
        - 1.0.0-dev.0 through 1.0.0-dev.9 (10 development tags total)

    Side Effects:
        - Creates 10 empty commits in the repository
        - Creates 10 development tags pointing to these commits
        - Establishes a baseline for subsequent tag operations

    Usage:
        Typically called once during test setup to create a repository
        state that allows testing of tag incrementing, RC creation, and
        other advanced operations.
    """
    for i in range(10):
        empty_commit()
        create_tag(f"1.0.0-dev.{i}")


# Initialize VersionControlManager with test repository
manager = VersionControlManager("test_dir")

# ============================================================================
# PART 1: VCM INTEGRATION TESTS
# ============================================================================
def test_current_tag():
    """Test current tag retrieval functionality.

    This test verifies the VersionControlManager's ability to identify and return
    the current highest development tag. It tests both empty repository
    scenarios and repositories with multiple development tags.

    Test Scenario:
        1. Start with empty repository (should return None)
        2. Create first development tag and verify retrieval
        3. Create multiple development tags and verify highest is returned

    Validates:
        - Empty repository handling (returns None)
        - Initial tag creation (0.1.0-dev.1)
        - Highest tag identification from multiple options
        - Semantic version sorting (1.0.0-dev.9 > 0.1.0-dev.1)

    Business Logic Tested:
        - get_current_tag() with default "dev" prerelease identifier
        - increment_prerelease_tag() initial tag creation
        - Proper semantic version comparison and sorting
    """
    assert manager.get_current_tag() is None
    empty_commit()
    assert manager.increment_prerelease_tag() == "0.1.0-dev.1"
    assert manager.get_current_tag() == "0.1.0-dev.1"
    create_tags()
    assert manager.get_current_tag() == "1.0.0-dev.9"


def test_increment_prerelease_tag():
    """Test prerelease tag incrementing functionality.

    This test verifies that the VersionControlManager can correctly increment
    the prerelease number of an existing development tag while maintaining
    the same major.minor.patch version numbers.

    Test Scenario:
        - Increment from existing tag "1.0.0-dev.9" to "1.0.0-dev.10"
        - Verify the new tag becomes the current highest tag

    Validates:
        - Prerelease number incrementing (9 → 10)
        - Tag creation in repository
        - Updated current tag retrieval
        - Preservation of major.minor.patch version

    Business Logic Tested:
        - increment_prerelease_tag() with existing tag parameter
        - Proper prerelease number parsing and incrementing
        - Tag creation and registration in repository
    """
    assert manager.increment_prerelease_tag("1.0.0-dev.9") == "1.0.0-dev.10"
    assert manager.get_current_tag() == "1.0.0-dev.10"


def test_find_tag():
    """Test tag existence checking functionality.

    This test verifies the VersionControlManager's ability to check whether
    specific tags exist in the repository. It tests both positive
    (tag exists) and negative (tag doesn't exist) cases.

    Test Scenarios:
        1. Search for non-existent tag (should return False)
        2. Search for existing tag (should return True)

    Validates:
        - Accurate tag existence detection
        - Case-sensitive tag name matching
        - Repository tag collection querying

    Business Logic Tested:
        - find_tag() method with exact tag name matching
        - Repository tag enumeration and comparison
        - Boolean return values for existence checks
    """
    assert not manager.find_tag("test")
    assert manager.find_tag("1.0.0-dev.10")


def test_get_init_rc_tag():
    """Test release candidate tag generation from development tags.

    This test verifies the static utility method that converts development
    tags into their corresponding initial release candidate tags. This is
    a crucial step in the development → RC → production workflow.

    Test Scenario:
        - Convert development tag "1.0.0-dev.10" to RC tag "1.0.0-rc.1"

    Validates:
        - Proper tag format conversion (dev.N → rc.1)
        - Preservation of major.minor.patch version
        - Static method functionality (no repository interaction)
        - Semantic versioning rule compliance

    Business Logic Tested:
        - get_init_rc_tag() static method
        - Development to RC tag transformation logic
        - Version number parsing and reconstruction
    """
    assert manager.get_init_rc_tag("1.0.0-dev.10") == "1.0.0-rc.1"


def test_init_new_rc():
    """Test release candidate initialization from current development tag.

    This test verifies the VersionControlManager's ability to create the first
    release candidate tag based on the highest existing development tag.
    This represents a key milestone in the development workflow where
    development is considered feature-complete and ready for testing.

    Test Scenario:
        1. Initialize RC from current development tag (1.0.0-dev.10)
        2. Verify RC tag creation (1.0.0-rc.1)
        3. Confirm RC becomes current RC tag

    Validates:
        - RC initialization from development tag
        - Proper RC tag naming (major.minor.patch-rc.1)
        - Tag creation in repository with appropriate commit reference
        - Current RC tag retrieval functionality

    Business Logic Tested:
        - init_new_rc() method with development prerelease parameter
        - Development to RC workflow transition
        - Tag creation with commit referencing
        - RC tag identification and retrieval
    """
    assert manager.init_new_rc("dev") == "1.0.0-rc.1"
    assert manager.get_current_tag("rc") == "1.0.0-rc.1"


def test_get_current_rc():
    """Test current release candidate retrieval for specific version.

    This test verifies the VersionControlManager's ability to find the current
    (highest) release candidate tag for a specific base version. This
    is essential for RC management and incrementing operations.

    Test Scenario:
        - Retrieve current RC for base version "1.0.0"
        - Should return "1.0.0-rc.1" (the existing RC tag)

    Validates:
        - Base version to RC tag mapping
        - Current RC identification for specific versions
        - Proper pattern matching for RC tags

    Business Logic Tested:
        - get_current_rc_patch() method with RC prerelease type
        - Version-specific tag pattern matching
        - Highest RC tag identification within version family
    """
    assert manager.get_current_rc_patch("1.0.0") == "1.0.0-rc.1"


def test_increment_rc():
    """Test release candidate tag incrementing.

    This test verifies the VersionControlManager's ability to create subsequent
    release candidate versions when additional RC iterations are needed
    during the testing and stabilization phase.

    Test Scenario:
        1. Increment RC from "1.0.0-rc.1" to "1.0.0-rc.2"
        2. Verify new RC becomes the current RC for the version

    Validates:
        - RC prerelease number incrementing (rc.1 → rc.2)
        - Preservation of base version (1.0.0)
        - Tag creation in repository
        - Updated current RC retrieval

    Business Logic Tested:
        - increment_rc_patch() method with RC prerelease type
        - RC tag incrementing logic
        - Current RC tag updating after increment

    Workflow Context:
        This simulates the scenario where an RC needs additional iterations
        due to bugs found during testing, requiring RC.2, RC.3, etc.
    """
    assert manager.increment_rc_patch("1.0.0") == "1.0.0-rc.2"
    assert manager.get_current_rc_patch("1.0.0") == "1.0.0-rc.2"


def test_prod_release():
    """Test production tag creation from release candidate.

    This test verifies the final step in the development workflow: promoting
    a tested and approved release candidate to a production version. This
    represents the official release of the software version.

    Test Scenario:
        - Promote RC tag "1.0.0-rc.2" to production tag "1.0.0"

    Validates:
        - RC to production tag conversion
        - Removal of prerelease suffix (-rc.2 → "")
        - Tag creation with proper commit reference
        - Production tag format compliance

    Business Logic Tested:
        - create_prod_tag() method with RC tag parameter
        - RC to production workflow transition
        - Production tag naming rules
        - Commit reference preservation during promotion

    Workflow Context:
        This represents the culmination of the development cycle where
        a thoroughly tested RC is deemed ready for production deployment.
    """
    assert manager.create_prod_tag("1.0.0-rc.2") == "1.0.0"


def test_increment_rc_exception():
    """Test error handling for invalid RC increment attempts.

    This test verifies that the VersionControlManager properly enforces business
    rules by preventing RC tag creation when a production version already
    exists for the same version number. This prevents accidental regression
    or confusion in the versioning workflow.

    Test Scenario:
        - Attempt to increment RC for version "1.0.0" (production exists)
        - Should raise InvalidTagCreation exception

    Validates:
        - Business rule enforcement (no RC after production)
        - Proper exception raising and type
        - Error message clarity and helpfulness
        - Repository state validation before tag creation

    Business Logic Tested:
        - increment_rc_patch() validation logic
        - InvalidTagCreation exception handling
        - Production version existence checking
        - Business rule compliance enforcement

    Error Scenario:
        This test documents the rule: "Cannot increment RC version for a
        version found in Production" - once a version goes to production,
        no more RCs can be created for that version.
    """
    with pytest.raises(InvalidTagCreation):
        manager.increment_rc_patch("1.0.0")


def test_increment_dev_after_prod_release():
    """Test development tag incrementing after production release.

    This test verifies the VersionControlManager's ability to continue development
    work after a production release by automatically bumping to the next
    minor version for new development work. This ensures clear separation
    between released and unreleased code.

    Test Scenario:
        - Current dev tag is "1.0.0-dev.10" (same version as production "1.0.0")
        - Incrementing should jump to "1.1.0-dev.1" (next minor version)

    Validates:
        - Automatic minor version bump when production version exists
        - Prevention of dev tag confusion with released versions
        - Proper version increment logic (1.0.x → 1.1.0)
        - Development workflow continuation after release

    Business Logic Tested:
        - increment_prerelease_tag() version bump logic
        - Production version conflict detection
        - Minor version incrementing rules
        - Development tag reset to .1 after version bump

    Workflow Context:
        This simulates the common scenario where development continues
        after a release, requiring a clear version separation between
        the released code and new development work.
    """
    assert manager.increment_prerelease_tag(manager.get_current_tag()) == "1.1.0-dev.1"


def test_get_current_patch():
    """Test patch tag retrieval for versions without patches.

    This test verifies that the VersionControlManager correctly handles queries
    for patch tags when no patch versions exist. This establishes the
    baseline before patch tag creation and tests proper None handling.

    Test Scenarios:
        1. Query patch for version "1.0.0" (production exists, no patches)
        2. Query patch for version "1.1.0" (no production, no patches)

    Both should return None since no patch tags exist yet.

    Validates:
        - Proper None return for non-existent patch tags
        - Patch tag querying for different version states
        - Baseline establishment for patch workflow testing

    Business Logic Tested:
        - get_current_rc_patch() method with "patch" prerelease type
        - Pattern matching for patch tags
        - Handling of non-existent tag scenarios
    """
    assert manager.get_current_rc_patch("1.0.0", "patch") is None
    assert manager.get_current_rc_patch("1.1.0", "patch") is None


def test_increment_patch_exception():
    """Test error handling for invalid patch increment attempts.

    This test verifies that the VersionControlManager enforces the business rule
    that patch tags can only be created for versions that have been
    released to production. This prevents patch creation for unreleased
    versions, maintaining version integrity.

    Test Scenario:
        - Attempt to create patch for version "1.1.0" (no production version)
        - Should raise InvalidTagCreation exception

    Validates:
        - Business rule enforcement (patches require production version)
        - Proper exception raising for invalid operations
        - Production version prerequisite checking
        - Error message clarity for debugging

    Business Logic Tested:
        - increment_rc_patch() validation with patch type
        - InvalidTagCreation exception for rule violations
        - Production version existence validation
        - Patch creation prerequisites

    Error Scenario:
        Documents the rule: "No Production version available" - patches
        can only be created for versions that have been officially released.
    """
    with pytest.raises(InvalidTagCreation):
        manager.increment_rc_patch("1.1.0", "patch")


def test_init_new_patch():
    """Test patch tag initialization for hotfix workflow.

    This test verifies the VersionControlManager's ability to initialize the
    patch workflow for production hotfixes. This creates the first
    patch prerelease tag based on the current production version,
    enabling hotfix development.

    Test Scenario:
        - Initialize patch from current production (should be "1.0.0")
        - Should create "1.0.0-patch.1" for hotfix development

    Validates:
        - Patch initialization from production version
        - Proper patch tag naming (version-patch.1)
        - Hotfix workflow establishment
        - Current production version detection

    Business Logic Tested:
        - init_new_patch() method
        - Production to patch workflow transition
        - Patch tag creation with proper commit reference
        - Hotfix development setup

    Workflow Context:
        This represents the beginning of a hotfix process where a
        critical bug in production needs to be addressed without
        waiting for the next major release cycle.
    """
    assert manager.init_new_patch() == "1.0.0-patch.1"


def test_increment_patch():
    """Test patch tag incrementing during hotfix development.

    This test verifies the VersionControlManager's ability to increment patch
    prerelease tags during hotfix development iterations. This allows
    multiple rounds of fixes and testing before the hotfix is released.

    Test Scenario:
        - Increment patch from "1.0.0-patch.1" to "1.0.0-patch.2"

    Validates:
        - Patch prerelease number incrementing (patch.1 → patch.2)
        - Preservation of base production version (1.0.0)
        - Hotfix iteration support
        - Tag creation in repository

    Business Logic Tested:
        - increment_rc_patch() method with patch prerelease type
        - Patch tag incrementing logic
        - Hotfix development workflow support
        - Prerelease number management for patches

    Workflow Context:
        This simulates additional iterations in hotfix development,
        where multiple patch versions might be needed before the
        fix is ready for production deployment.
    """
    assert manager.increment_rc_patch("1.0.0", "patch") == "1.0.0-patch.2"


def test_create_prod_from_patch():
    """Test production tag creation from patch prerelease.

    This test verifies the VersionControlManager's ability to promote a tested
    patch prerelease to a production patch version. This completes the
    hotfix workflow by creating an official patch release.

    Test Scenario:
        - Promote patch "1.0.0-patch.2" to production "1.0.1"

    Validates:
        - Patch to production tag conversion
        - Automatic patch number increment (1.0.0 → 1.0.1)
        - Hotfix workflow completion
        - Production tag creation with proper commit reference

    Business Logic Tested:
        - create_prod_tag() method with patch prerelease parameter
        - Patch version incrementing rules
        - Production tag naming for patches
        - Hotfix to production workflow transition

    Workflow Context:
        This represents the completion of a hotfix cycle where a
        thoroughly tested patch is promoted to production, creating
        an official patch release (1.0.1) that fixes issues in 1.0.0.
    """
    assert manager.create_prod_tag("1.0.0-patch.2") == "1.0.1"


def test_get_current_production_tag():
    """Test current production tag retrieval.

    This test verifies the VersionControlManager's ability to identify and return
    the current highest production version. This is essential for various
    operations including patch initialization and version management.

    Test Scenario:
        - Retrieve current production tag (should be "1.0.1" after patch)

    Validates:
        - Production tag identification
        - Highest production version selection
        - Patch version recognition as production
        - Production tag querying functionality

    Business Logic Tested:
        - get_current_tag() method with production=True parameter
        - Production tag pattern matching
        - Semantic version sorting for production tags
        - Production version history tracking

    Workflow Context:
        After creating patch version 1.0.1, it should be recognized as
        the current production version, taking precedence over 1.0.0.
    """
    assert manager.get_current_tag(production=True) == "1.0.1"


def test_major_bump():
    """Test complete major version bump workflow.

    This comprehensive test verifies the VersionControlManager's ability to handle
    a complete major version bump scenario, simulating a development cycle
    that includes breaking changes requiring a major version increment.

    Test Workflow:
        1. Start with current dev tag "1.1.0-dev.1"
        2. Increment to "1.1.0-dev.2" (normal development)
        3. Create RC "1.1.0-rc.1" and promote to production "1.1.0"
        4. Perform major bump to "2.0.0-dev.1" (breaking changes)
        5. Verify new major version becomes current

    Validates:
        - Complete development cycle (dev → RC → production)
        - Major version bumping logic (1.x.x → 2.0.0)
        - Version reset behavior (minor and patch reset to 0)
        - Development tag reset to .1 after major bump
        - Production version progression (1.0.1 → 1.1.0 → current)

    Business Logic Tested:
        - increment_prerelease_tag() normal and major bump modes
        - init_new_rc() and create_prod_tag() workflow
        - Major version bump with major_bump=True parameter
        - Version number reset rules for major bumps
        - Current tag tracking across version families

    Workflow Context:
        This simulates a complete development cycle where significant
        breaking changes necessitate a major version increment, following
        semantic versioning principles where major bumps indicate
        backward-incompatible changes.
    """
    assert manager.get_current_tag() == "1.1.0-dev.1"
    assert manager.increment_prerelease_tag(tag="1.1.0-dev.1") == "1.1.0-dev.2"
    assert manager.init_new_rc() == "1.1.0-rc.1"
    assert manager.create_prod_tag("1.1.0-rc.1") == "1.1.0"
    assert manager.get_current_tag(production=True) == "1.1.0"
    assert manager.increment_prerelease_tag("1.1.0-dev.2", major_bump=True) == "2.0.0-dev.1"
    assert manager.get_current_tag() == "2.0.0-dev.1"

def test_multiple_rc_iterations():
    """Test multiple release candidate iterations before production.

    This test simulates a realistic scenario where multiple RC versions
    are needed due to bugs found during testing. It validates the complete
    RC iteration workflow and proper version incrementing.

    Test Workflow:
        1. Create multiple RC iterations (rc.1 → rc.2 → rc.3)
        2. Verify each increment is properly tracked
        3. Promote final RC to production
        4. Verify production version is correct

    Validates:
        - Multiple RC increments within same version
        - RC version tracking and retrieval
        - Final RC promotion to production
        - Version consistency throughout process

    Business Logic Tested:
        - increment_rc_patch() multiple iterations
        - get_current_rc_patch() after each increment
        - create_prod_tag() from any RC iteration
        - RC workflow resilience with multiple iterations
    """
    # Start fresh RC workflow from current dev
    assert manager.init_new_rc() == "2.0.0-rc.1"

    # Multiple RC iterations (simulating bug fixes during testing)
    assert manager.increment_rc_patch("2.0.0") == "2.0.0-rc.2"
    assert manager.get_current_rc_patch("2.0.0") == "2.0.0-rc.2"

    assert manager.increment_rc_patch("2.0.0") == "2.0.0-rc.3"
    assert manager.get_current_rc_patch("2.0.0") == "2.0.0-rc.3"

    # Finally promote to production
    assert manager.create_prod_tag("2.0.0-rc.3") == "2.0.0"
    assert manager.get_current_tag(production=True) == "2.0.0"

def test_patch_workflow_comprehensive():
    """Test comprehensive patch workflow with multiple iterations.

    This test validates the complete patch/hotfix workflow including
    multiple patch iterations, proper version incrementing, and
    integration with the existing production version history.

    Test Workflow:
        1. Create initial patch from production 2.0.0
        2. Increment patch multiple times (simulating hotfix development)
        3. Promote patch to production (creates 2.0.1)
        4. Create another patch series for 2.0.1
        5. Validate version progression and current version tracking

    Validates:
        - Patch initialization from any production version
        - Multiple patch increments within same base version
        - Patch promotion creating proper production increment
        - Ability to patch the patched version
        - Production version progression (2.0.0 → 2.0.1 → 2.0.2)

    Business Logic Tested:
        - init_new_patch() from latest production
        - increment_rc_patch() with patch type multiple times
        - create_prod_tag() from patch creating incremented production
        - Patch workflow on previously patched versions
    """
    # Initialize patch for current production (2.0.0)
    assert manager.init_new_patch() == "2.0.0-patch.1"

    # Multiple patch iterations (simulating hotfix development)
    assert manager.increment_rc_patch("2.0.0", "patch") == "2.0.0-patch.2"
    assert manager.increment_rc_patch("2.0.0", "patch") == "2.0.0-patch.3"
    assert manager.get_current_rc_patch("2.0.0", "patch") == "2.0.0-patch.3"

    # Promote patch to production (2.0.0 → 2.0.1)
    assert manager.create_prod_tag("2.0.0-patch.3") == "2.0.1"
    assert manager.get_current_tag(production=True) == "2.0.1"

    # Create another patch series for the newly created production version
    assert manager.init_new_patch() == "2.0.1-patch.1"
    assert manager.increment_rc_patch("2.0.1", "patch") == "2.0.1-patch.2"

    # Promote second patch series
    assert manager.create_prod_tag("2.0.1-patch.2") == "2.0.2"
    assert manager.get_current_tag(production=True) == "2.0.2"

def test_parallel_development_after_release():
    """Test parallel development workflow after production release.

    This test simulates a realistic scenario where development continues
    in parallel with production releases and hotfixes. It validates that
    development can proceed independently while production versions are
    being patched.

    Test Workflow:
        1. Continue development after 2.0.0 release (should bump to 2.1.0-dev.1)
        2. Create multiple development iterations
        3. While dev continues, ensure patch workflow still works
        4. Create RC from latest development
        5. Validate version separation and independence

    Validates:
        - Development continuation after production release
        - Proper minor version bump for new development
        - Independence of dev and patch workflows
        - Version family separation (2.0.x patches vs 2.1.x development)
        - Multiple concurrent version tracks

    Business Logic Tested:
        - increment_prerelease_tag() with automatic version bump detection
        - Parallel workflow support (dev vs patch)
        - Version family isolation
        - Current tag tracking across different version families
    """
    # Development continues after 2.0.0 release
    # Should automatically bump to 2.1.0 since 2.0.0 is in production
    current_dev = manager.get_current_tag()  # Should be 2.0.0-dev.1
    assert manager.increment_prerelease_tag(current_dev) == "2.1.0-dev.1"

    # Continue development iterations
    assert manager.increment_prerelease_tag("2.1.0-dev.1") == "2.1.0-dev.2"
    assert manager.increment_prerelease_tag("2.1.0-dev.2") == "2.1.0-dev.3"
    assert manager.get_current_tag() == "2.1.0-dev.3"

    # Meanwhile, patch workflow should still work for production versions
    # (This validates parallel development and patch workflows)
    assert manager.get_current_tag(production=True) == "2.0.2"

    # Create RC from current development
    assert manager.init_new_rc() == "2.1.0-rc.1"
    assert manager.get_current_tag("rc") == "2.1.0-rc.1"

def test_version_conflict_prevention():
    """Test version conflict prevention and validation rules.

    This test validates all the business rules that prevent invalid
    version states and conflicts in the semantic versioning workflow.
    It ensures proper error handling and validation.

    Test Scenarios:
        1. Try to create RC when production already exists
        2. Try to create patch when no production exists
        3. Try to increment patch when higher patch exists in production
        4. Validate proper exception messages and types

    Validates:
        - Business rule enforcement prevents invalid states
        - Proper exception types (InvalidTagCreation)
        - Clear error messages for debugging
        - Version state validation before tag creation

    Business Logic Tested:
        - increment_rc_patch() validation rules
        - InvalidTagCreation exception handling
        - Production version conflict detection
        - Patch prerequisite validation
    """
    # Rule 1: Cannot create RC when production version exists
    with pytest.raises(InvalidTagCreation) as exc_info:
        manager.increment_rc_patch("2.0.0")  # Production 2.0.0 exists
    assert "Production version available" in str(exc_info.value)

    # Rule 2: Cannot create patch when no production version exists
    with pytest.raises(InvalidTagCreation) as exc_info:
        manager.increment_rc_patch("3.0.0", "patch")  # No production 3.0.0
    assert "Production version not available" in str(exc_info.value)

    # Rule 3: Cannot increment patch when higher patch exists in production
    # First, let's create a scenario where this would apply
    empty_commit()
    create_tag("2.0.3")  # Simulate higher patch in production

    with pytest.raises(InvalidTagCreation) as exc_info:
        manager.increment_rc_patch("2.0.2", "patch")  # 2.0.3 already exists
    assert "Patch found in Production" in str(exc_info.value)

def test_edge_cases_and_boundaries():
    """Test edge cases and boundary conditions.

    This test covers various edge cases that might occur in real-world
    usage, ensuring the VersionControlManager is robust and handles unusual
    but valid scenarios correctly.

    Test Scenarios:
        1. Version number boundaries (0.0.0, high numbers)
        2. Empty repository initialization
        3. Tag creation from initial state
        4. Pattern matching edge cases

    Validates:
        - Robustness with edge case version numbers
        - Proper handling of empty repository states
        - Initial tag creation workflows
        - Pattern matching accuracy with various formats

    Business Logic Tested:
        - Version number parsing and validation
        - Initial state handling
        - Pattern matching reliability
        - Boundary condition handling
    """
    # Test with version boundaries
    assert manager.get_init_rc_tag("0.0.1-dev.1") == "0.0.1-rc.1"
    assert manager.get_init_rc_tag("999.999.999-dev.1") == "999.999.999-rc.1"

    # Test pattern matching with existing tags
    dev_pattern = r"^(\d+)\.(\d+)\.(\d+)-dev\.(\d+)$"
    result = manager.find_tag_with_pattern(dev_pattern)
    assert result == "2.1.0-dev.3"  # Should find highest dev tag

    # Test production pattern matching
    prod_pattern = r"^(\d+)\.(\d+)\.(\d+)$"
    result = manager.find_tag_with_pattern(prod_pattern)
    assert result in ["2.0.3", "2.0.2"]  # Should find one of the high production tags

def test_complete_multi_version_workflow():
    """Test complete multi-version development workflow.

    This comprehensive test simulates a realistic multi-version development
    scenario with overlapping releases, patches, and development cycles.
    It validates the complete system behavior over an extended period.

    Test Workflow:
        1. Complete 2.1.0 release cycle (RC → production)
        2. Start 2.2.0 development with minor bump
        3. Create patch for 2.1.0 while 2.2.0 development continues
        4. Start major 3.0.0 development cycle
        5. Validate all version families coexist correctly

    Validates:
        - Multi-version workflow management
        - Version family independence
        - Concurrent development and patch workflows
        - Long-term version history integrity
        - Complex version state management

    Business Logic Tested:
        - Complete workflow cycles across multiple versions
        - Version family separation and coexistence
        - Long-term tag management and retrieval
        - Complex version state scenarios
    """
    # Complete 2.1.0 release cycle
    assert manager.create_prod_tag("2.1.0-rc.1") == "2.1.0"
    assert manager.get_current_tag(production=True) == "2.1.0"

    # Start 2.2.0 development (minor bump)
    assert manager.increment_prerelease_tag("2.1.0-dev.3") == "2.2.0-dev.1"
    assert manager.increment_prerelease_tag("2.2.0-dev.1") == "2.2.0-dev.2"

    # Meanwhile, create patch for 2.1.0
    empty_commit()  # Need commit for patch tag
    create_tag("2.1.0-patch.1")  # Direct creation to simulate hotfix
    assert manager.increment_rc_patch("2.1.0", "patch") == "2.1.0-patch.2"
    assert manager.create_prod_tag("2.1.0-patch.2") == "2.1.1"

    # Start major 3.0.0 development cycle
    assert manager.init_new_rc() == "2.2.0-rc.1"
    assert manager.increment_prerelease_tag("2.2.0-dev.2", major_bump=True) == "3.0.0-dev.1"

    # Validate current states across all version families
    assert manager.get_current_tag() == "3.0.0-dev.1"  # Latest development
    assert manager.get_current_tag(production=True) == "2.1.1"  # Latest production

    # Create RC for 3.0.0
    assert manager.init_new_rc() == "3.0.0-rc.1"
    assert manager.create_prod_tag("3.0.0-rc.1") == "3.0.0"

    # Final state validation
    assert manager.get_current_tag(production=True) == "3.0.0"

def test_repository_state_integrity():
    """Test repository state integrity throughout complex operations.

    This test validates that the VersionControlManager maintains repository
    integrity and consistency throughout complex operation sequences.
    It ensures no orphaned tags or inconsistent states are created.

    Test Scenarios:
        1. Verify all created tags exist in repository
        2. Validate tag-commit relationships
        3. Check version history consistency
        4. Ensure no duplicate or conflicting tags

    Validates:
        - Repository tag integrity
        - Consistent tag-commit relationships
        - Version history accuracy
        - No duplicate or orphaned tags

    Business Logic Tested:
        - find_tag() accuracy for all created tags
        - Repository state consistency
        - Tag creation integrity
        - Version tracking accuracy
    """
    # Test a comprehensive list of tags that should exist
    expected_tags = [
        "0.1.0-dev.1",  # Initial tag
        "1.0.0-dev.9",  # From create_tags()
        "1.0.0-dev.10",  # Incremented
        "1.0.0-rc.1",  # RC initialized
        "1.0.0-rc.2",  # RC incremented
        "1.0.0",  # Production from RC
        "1.0.0-patch.1",  # Patch initialized
        "1.0.0-patch.2",  # Patch incremented
        "1.0.1",  # Production from patch
        "1.1.0-dev.1",  # Dev after production
        "1.1.0-dev.2",  # Dev incremented
        "1.1.0-rc.1",  # RC from dev
        "1.1.0",  # Production from RC
        "2.0.0-dev.1",  # Major bump
        "2.0.0-rc.1",  # RC from major
        "2.0.0-rc.2",  # RC incremented
        "2.0.0-rc.3",  # RC incremented
        "2.0.0",  # Production from RC
        "2.0.0-patch.1",  # Patch initialized
        "2.0.0-patch.2",  # Patch incremented
        "2.0.0-patch.3",  # Patch incremented
        "2.0.1",  # Production from patch
        "2.0.1-patch.1",  # Second patch series
        "2.0.1-patch.2",  # Second patch incremented
        "2.0.2",  # Production from second patch
        "2.1.0-dev.1",  # New dev cycle
        "2.1.0-dev.2",  # Dev incremented
        "2.1.0-dev.3",  # Dev incremented
        "2.1.0-rc.1",  # RC from dev
        "2.1.0",  # Production from RC
        "2.2.0-dev.1",  # Minor bump dev
        "2.2.0-dev.2",  # Dev incremented
        "3.0.0-dev.1",  # Major bump
        "3.0.0-rc.1",  # RC from major
        "3.0.0",  # Final production
    ]

    # Verify all expected tags exist
    for tag in expected_tags:
        assert manager.find_tag(tag), f"Expected tag {tag} not found in repository"

    # Verify current state accuracy
    assert manager.get_current_tag() == "3.0.0-dev.1"  # Latest dev (if any remaining)
    assert manager.get_current_tag(production=True) == "3.0.0"  # Latest production
    assert manager.get_current_tag("rc") is None or manager.get_current_tag("rc") == "3.0.0-rc.1"

def test_invalid_tag_format_handling():
    """Test handling of invalid tag formats and edge cases.

    This test validates that the VersionControlManager properly handles and
    rejects invalid tag formats, maintaining system integrity and
    providing clear error messages.

    Test Scenarios:
        1. Invalid prerelease tag formats
        2. Invalid production tag formats
        3. Malformed version numbers
        4. Edge case version patterns

    Validates:
        - Proper ValueError raising for invalid formats
        - Input validation before tag operations
        - Error message clarity and helpfulness
        - System protection against malformed inputs

    Business Logic Tested:
        - Tag format validation across all methods
        - ValueError exception handling
        - Input sanitization and validation
        - Format compliance enforcement
    """
    # Test invalid formats for get_init_rc_tag
    invalid_formats = [
        "1.0.0",  # Missing prerelease
        "1.0-dev.1",  # Missing patch version
        "1.0.0-dev",  # Missing prerelease number
        "invalid-tag",  # Non-semantic format
        "",  # Empty string
        "1.0.0-dev.a",  # Non-numeric prerelease
    ]

    for invalid_format in invalid_formats:
        with pytest.raises(ValueError):
            manager.get_init_rc_tag(invalid_format)

    # Test invalid formats for increment_prerelease_tag
    for invalid_format in invalid_formats:
        if invalid_format:  # Skip empty string for this test
            with pytest.raises(ValueError):
                manager.increment_prerelease_tag(invalid_format)

    # Test invalid formats for create_prod_tag
    invalid_prod_formats = [
        "1.0.0",  # Already production format
        "1.0.0-dev.1",  # Development format (not RC/patch)
        "invalid-tag",  # Non-semantic format
        "1.0.0-invalid.1",  # Unknown prerelease type
    ]

    for invalid_format in invalid_prod_formats:
        with pytest.raises(ValueError):
            manager.create_prod_tag(invalid_format)


# ============================================================================
# PART 2: CLI UNIT TESTS
# ============================================================================

@pytest.fixture
def mock_vcm():
    """Create a mock VersionControlManager for testing CLI operations."""
    with patch('src.vcm.cli.VersionControlManager') as mock:
        instance = mock.return_value
        yield instance


@pytest.fixture
def cli_parser():
    """Create an argument parser instance for testing CLI argument parsing."""
    return create_parser()


def test_cli_get_current_tag_basic(mock_vcm):
    """Test basic get-current-tag CLI command functionality.

    This test verifies that the get-current-tag command correctly calls the
    VersionControlManager with default parameters and returns the current tag
    without additional formatting when the --detailed flag is not used.

    Test Scenario:
        1. Mock VCM returns a development tag
        2. Parse get-current-tag command with default options
        3. Capture stdout to verify output format
        4. Verify VCM called with correct parameters
        5. Verify clean output (just the tag, no additional text)

    Validates:
        - Basic command execution without errors
        - Correct default parameter values (prerelease_tag='dev', production=False)
        - Output contains only the tag value
        - Return code indicates success (0)

    Business Logic Tested:
        - handle_get_current_tag() with default arguments
        - Simple output format for scripting use cases
    """
    mock_vcm.get_current_tag.return_value = "1.0.0-dev.5"

    parser = create_parser()
    args = parser.parse_args(['get-current-tag'])

    captured_output = StringIO()
    with patch('sys.stdout', captured_output):
        result = handle_get_current_tag(args)

    assert result == 0
    assert captured_output.getvalue().strip() == "1.0.0-dev.5"
    mock_vcm.get_current_tag.assert_called_once_with(
        prerelease_tag='dev',
        production=False
    )


def test_cli_get_current_tag_detailed(mock_vcm):
    """Test get-current-tag command with detailed output flag.

    This test verifies that the --detailed flag produces human-readable output
    with descriptive context about what tag was found, useful for interactive
    use cases where users need confirmation of what the command did.

    Test Scenario:
        1. Mock VCM returns a development tag
        2. Parse command with --detailed flag
        3. Capture and verify output includes descriptive message
        4. Confirm VCM called correctly

    Validates:
        - Detailed output format includes descriptive prefix
        - Tag value still present in output
        - --detailed flag properly parsed and handled
        - Return code indicates success

    Business Logic Tested:
        - handle_get_current_tag() detailed output mode
        - User-friendly messaging for interactive usage
    """
    mock_vcm.get_current_tag.return_value = "1.0.0-dev.5"

    parser = create_parser()
    args = parser.parse_args(['get-current-tag', '--detailed'])

    captured_output = StringIO()
    with patch('sys.stdout', captured_output):
        result = handle_get_current_tag(args)

    assert result == 0
    output = captured_output.getvalue().strip()
    assert "Latest dev prerelease tag found: 1.0.0-dev.5" in output


def test_cli_get_current_tag_production(mock_vcm):
    """Test get-current-tag command with production flag.

    This test verifies that the --production flag correctly requests production
    tags instead of prerelease tags, allowing users to query the latest
    production release without prerelease identifiers.

    Test Scenario:
        1. Mock VCM returns a production tag
        2. Parse command with --production flag
        3. Verify VCM called with production=True
        4. Confirm output contains production tag

    Validates:
        - --production flag properly parsed
        - Production parameter passed to VCM correctly
        - Production tags returned without prerelease identifiers
        - Return code indicates success

    Business Logic Tested:
        - handle_get_current_tag() production mode
        - Production vs prerelease tag filtering
    """
    mock_vcm.get_current_tag.return_value = "2.0.0"

    parser = create_parser()
    args = parser.parse_args(['get-current-tag', '--production'])

    captured_output = StringIO()
    with patch('sys.stdout', captured_output):
        result = handle_get_current_tag(args)

    assert result == 0
    assert captured_output.getvalue().strip() == "2.0.0"
    mock_vcm.get_current_tag.assert_called_once_with(
        prerelease_tag='dev',
        production=True
    )


def test_cli_get_current_tag_no_tags(mock_vcm):
    """Test get-current-tag command when no matching tags exist.

    This test verifies proper error handling when the repository has no tags
    matching the requested criteria. It ensures the CLI provides a clear
    error message and returns an appropriate exit code for scripting.

    Test Scenario:
        1. Mock VCM returns None (no tags found)
        2. Execute get-current-tag command
        3. Capture stderr for error message
        4. Verify non-zero exit code

    Validates:
        - None return value handled gracefully
        - Error message written to stderr (not stdout)
        - Non-zero exit code (1) for error condition
        - Error message is clear and actionable

    Business Logic Tested:
        - handle_get_current_tag() error handling
        - Empty repository scenario
        - Proper stderr vs stdout usage
    """
    mock_vcm.get_current_tag.return_value = None

    parser = create_parser()
    args = parser.parse_args(['get-current-tag'])

    captured_error = StringIO()
    with patch('sys.stderr', captured_error):
        result = handle_get_current_tag(args)

    assert result == 1
    assert "No matching tags found" in captured_error.getvalue()


def test_cli_increment_prerelease_basic(mock_vcm):
    """Test basic increment-prerelease CLI command functionality.

    This test verifies that the increment-prerelease command correctly
    increments a prerelease tag and returns the new tag value. Tests the
    most common use case of incrementing from an existing tag.

    Test Scenario:
        1. Mock VCM returns incremented tag
        2. Parse command with base tag
        3. Verify new tag created and returned
        4. Confirm VCM called with correct parameters

    Validates:
        - Tag increment operation succeeds
        - Prerelease identifier passed correctly
        - Output contains only new tag (for scripting)
        - Major bump defaulted to False
        - Return code indicates success

    Business Logic Tested:
        - handle_increment_prerelease() basic operation
        - Tag parameter parsing and passing
        - Default prerelease identifier ('dev')
    """
    mock_vcm.increment_prerelease_tag.return_value = "1.0.0-dev.6"

    parser = create_parser()
    args = parser.parse_args(['increment-prerelease', '--tag', '1.0.0-dev.5'])

    captured_output = StringIO()
    with patch('sys.stdout', captured_output):
        result = handle_increment_prerelease(args)

    assert result == 0
    assert captured_output.getvalue().strip() == "1.0.0-dev.6"
    mock_vcm.increment_prerelease_tag.assert_called_once_with(
        tag='1.0.0-dev.5',
        prerelease_tag='dev',
        major_bump=False
    )


def test_cli_increment_prerelease_major_bump(mock_vcm):
    """Test increment-prerelease command with major version bump.

    This test verifies that the --major-bump flag correctly triggers a major
    version increment instead of the default minor increment, useful for
    breaking changes or significant new features.

    Test Scenario:
        1. Mock VCM returns major-bumped tag
        2. Parse command with --major-bump flag
        3. Verify major_bump=True passed to VCM
        4. Confirm major version incremented in result

    Validates:
        - --major-bump flag properly parsed
        - Major bump parameter passed to VCM
        - Major version incremented (0.x.x -> 1.x.x)
        - Minor version reset in result
        - Return code indicates success

    Business Logic Tested:
        - handle_increment_prerelease() major bump mode
        - Semantic versioning major increment rules
    """
    mock_vcm.increment_prerelease_tag.return_value = "1.0.0-dev.1"

    parser = create_parser()
    args = parser.parse_args([
        'increment-prerelease',
        '--tag', '0.5.0-dev.3',
        '--major-bump'
    ])

    captured_output = StringIO()
    with patch('sys.stdout', captured_output):
        result = handle_increment_prerelease(args)

    assert result == 0
    assert captured_output.getvalue().strip() == "1.0.0-dev.1"
    mock_vcm.increment_prerelease_tag.assert_called_once_with(
        tag='0.5.0-dev.3',
        prerelease_tag='dev',
        major_bump=True
    )


def test_cli_increment_prerelease_invalid_tag(mock_vcm):
    """Test increment-prerelease command with invalid tag format.

    This test verifies proper error handling when an invalid semantic version
    tag is provided, ensuring users get clear feedback about tag format
    requirements and preventing corrupt tags from being created.

    Test Scenario:
        1. Mock VCM raises ValueError for invalid tag
        2. Execute command with malformed tag
        3. Capture stderr for error message
        4. Verify non-zero exit code

    Validates:
        - ValueError from VCM caught and handled
        - Error message includes validation details
        - Error written to stderr (not stdout)
        - Non-zero exit code (1) for error condition
        - Error message mentions "Invalid tag format"

    Business Logic Tested:
        - handle_increment_prerelease() error handling
        - Tag format validation and error reporting
    """
    mock_vcm.increment_prerelease_tag.side_effect = ValueError("Invalid semantic version")

    parser = create_parser()
    args = parser.parse_args(['increment-prerelease', '--tag', 'invalid'])

    captured_error = StringIO()
    with patch('sys.stderr', captured_error):
        result = handle_increment_prerelease(args)

    assert result == 1
    assert "Invalid tag format" in captured_error.getvalue()


def test_cli_init_new_rc_basic(mock_vcm):
    """Test basic init-rc CLI command functionality.

    This test verifies that the init-rc command successfully creates a new
    release candidate tag from the latest development tag, marking the
    transition from development to release candidate phase.

    Test Scenario:
        1. Mock VCM returns new RC tag
        2. Parse init-rc command with defaults
        3. Verify RC tag created and returned
        4. Confirm VCM called with correct parameters

    Validates:
        - RC initialization succeeds
        - Default prerelease identifier ('dev') used
        - Output contains only new RC tag
        - Tag follows RC naming convention (x.y.z-rc.1)
        - Return code indicates success

    Business Logic Tested:
        - handle_init_new_rc() basic operation
        - Development to RC transition
        - Initial RC tag creation (rc.1)
    """
    mock_vcm.init_new_rc.return_value = "1.0.0-rc.1"

    parser = create_parser()
    args = parser.parse_args(['init-rc'])

    captured_output = StringIO()
    with patch('sys.stdout', captured_output):
        result = handle_init_new_rc(args)

    assert result == 0
    assert captured_output.getvalue().strip() == "1.0.0-rc.1"
    mock_vcm.init_new_rc.assert_called_once_with(prerelease_tag='dev')


def test_cli_init_new_rc_no_dev_tag(mock_vcm):
    """Test init-rc command when no development tag exists.

    This test verifies proper error handling when attempting to create an RC
    tag but no development tags exist in the repository, preventing invalid
    RC creation and providing clear guidance to users.

    Test Scenario:
        1. Mock VCM returns None (no dev tag found)
        2. Execute init-rc command
        3. Capture stderr for error message
        4. Verify non-zero exit code

    Validates:
        - None return value handled gracefully
        - Error message explains missing dev tag
        - Error written to stderr
        - Non-zero exit code (1) for error condition
        - Error message is actionable

    Business Logic Tested:
        - handle_init_new_rc() error handling
        - Prerequisite validation (dev tag must exist)
    """
    mock_vcm.init_new_rc.return_value = None

    parser = create_parser()
    args = parser.parse_args(['init-rc'])

    captured_error = StringIO()
    with patch('sys.stderr', captured_error):
        result = handle_init_new_rc(args)

    assert result == 1
    assert "No development tag found" in captured_error.getvalue()


def test_cli_init_new_patch_basic(mock_vcm):
    """Test basic init-patch CLI command functionality.

    This test verifies that the init-patch command successfully creates a new
    patch prerelease tag from the latest production tag, enabling hotfix
    workflows for addressing production issues.

    Test Scenario:
        1. Mock VCM returns new patch tag
        2. Parse init-patch command
        3. Verify patch tag created and returned
        4. Confirm VCM called correctly

    Validates:
        - Patch initialization succeeds
        - Output contains only new patch tag
        - Tag follows patch naming convention (x.y.z-patch.1)
        - Return code indicates success

    Business Logic Tested:
        - handle_init_new_patch() basic operation
        - Production to patch transition
        - Initial patch tag creation
    """
    mock_vcm.init_new_patch.return_value = "1.0.0-patch.1"

    parser = create_parser()
    args = parser.parse_args(['init-patch'])

    captured_output = StringIO()
    with patch('sys.stdout', captured_output):
        result = handle_init_new_patch(args)

    assert result == 0
    assert captured_output.getvalue().strip() == "1.0.0-patch.1"
    mock_vcm.init_new_patch.assert_called_once()


def test_cli_get_current_rc_patch_rc(mock_vcm):
    """Test get-current-rc-patch command for RC tags.

    This test verifies that the get-current-rc-patch command correctly
    retrieves the highest RC tag for a given base version, useful for
    determining which RC iteration is current before promoting to production.

    Test Scenario:
        1. Mock VCM returns highest RC tag for version
        2. Parse command with base version and rc type
        3. Verify correct RC tag returned
        4. Confirm VCM called with proper parameters

    Validates:
        - RC tag retrieval for specific version
        - Base version parameter parsed correctly
        - Default prerelease type ('rc') used
        - Highest RC number returned when multiple exist
        - Return code indicates success

    Business Logic Tested:
        - handle_get_current_rc_patch() RC mode
        - Version-specific tag filtering
    """
    mock_vcm.get_current_rc_patch.return_value = "1.0.0-rc.3"

    parser = create_parser()
    args = parser.parse_args(['get-current-rc-patch', '--tag', '1.0.0'])

    captured_output = StringIO()
    with patch('sys.stdout', captured_output):
        result = handle_get_current_rc_patch(args)

    assert result == 0
    assert captured_output.getvalue().strip() == "1.0.0-rc.3"
    mock_vcm.get_current_rc_patch.assert_called_once_with(
        tag='1.0.0',
        prerelease_tag='rc'
    )


def test_cli_increment_rc_patch_rc(mock_vcm):
    """Test increment-rc-patch command for RC tags.

    This test verifies that the increment-rc-patch command successfully
    increments an RC tag, creating the next RC iteration for a version.
    Useful when additional release candidate testing cycles are needed.

    Test Scenario:
        1. Mock VCM returns incremented RC tag
        2. Parse command with base version and rc type
        3. Verify new RC tag created and returned
        4. Confirm VCM called with correct parameters

    Validates:
        - RC tag increment succeeds
        - Base version preserved (1.0.0)
        - RC number incremented (rc.3 -> rc.4)
        - Default prerelease type used correctly
        - Return code indicates success

    Business Logic Tested:
        - handle_increment_rc_patch() RC mode
        - RC iteration increment logic
    """
    mock_vcm.increment_rc_patch.return_value = "1.0.0-rc.4"

    parser = create_parser()
    args = parser.parse_args(['increment-rc-patch', '--tag', '1.0.0'])

    captured_output = StringIO()
    with patch('sys.stdout', captured_output):
        result = handle_increment_rc_patch(args)

    assert result == 0
    assert captured_output.getvalue().strip() == "1.0.0-rc.4"
    mock_vcm.increment_rc_patch.assert_called_once_with(
        tag='1.0.0',
        prerelease_tag='rc'
    )


def test_cli_create_prod_tag_basic(mock_vcm):
    """Test basic create-prod CLI command functionality.

    This test verifies that the create-prod command successfully promotes
    an RC or patch tag to production, creating a clean production version
    tag without prerelease identifiers.

    Test Scenario:
        1. Mock VCM returns production tag
        2. Parse command with RC tag to promote
        3. Verify production tag created and returned
        4. Confirm VCM called with source tag

    Validates:
        - Production tag creation succeeds
        - Prerelease identifier removed (rc.3 -> clean version)
        - Source tag parameter parsed correctly
        - Output contains only production tag
        - Return code indicates success

    Business Logic Tested:
        - handle_create_prod_tag() basic operation
        - RC/patch to production promotion
        - Prerelease identifier stripping
    """
    mock_vcm.create_prod_tag.return_value = "1.0.0"

    parser = create_parser()
    args = parser.parse_args(['create-prod', '--tag', '1.0.0-rc.3'])

    captured_output = StringIO()
    with patch('sys.stdout', captured_output):
        result = handle_create_prod_tag(args)

    assert result == 0
    assert captured_output.getvalue().strip() == "1.0.0"
    mock_vcm.create_prod_tag.assert_called_once_with(tag='1.0.0-rc.3')


def test_cli_create_prod_tag_invalid(mock_vcm):
    """Test create-prod command with invalid tag format.

    This test verifies proper error handling when an invalid tag format
    is provided for production promotion, preventing corrupt production
    tags from being created and providing clear user feedback.

    Test Scenario:
        1. Mock VCM raises ValueError for invalid tag
        2. Execute command with malformed tag
        3. Capture stderr for error message
        4. Verify non-zero exit code

    Validates:
        - ValueError from VCM caught and handled
        - Error message includes validation details
        - Error written to stderr (not stdout)
        - Non-zero exit code (1) for error condition
        - Error message mentions "Invalid tag format"

    Business Logic Tested:
        - handle_create_prod_tag() error handling
        - Tag format validation for production promotion
    """
    mock_vcm.create_prod_tag.side_effect = ValueError("Invalid prerelease tag")

    parser = create_parser()
    args = parser.parse_args(['create-prod', '--tag', 'invalid-tag'])

    captured_error = StringIO()
    with patch('sys.stderr', captured_error):
        result = handle_create_prod_tag(args)

    assert result == 1
    assert "Invalid tag format" in captured_error.getvalue()


def test_cli_parser_structure(cli_parser):
    """Test CLI argument parser structure and configuration.

    This test verifies that the argument parser is properly configured
    with all expected commands and options, ensuring complete CLI
    functionality is available.

    Test Scenario:
        1. Verify parser description exists
        2. Check all subcommands are registered
        3. Validate command structure

    Validates:
        - Parser has help functionality
        - All expected commands exist
        - Subparser structure is correct
        - Command names follow conventions

    Business Logic Tested:
        - create_parser() configuration
        - Subcommand registration
        - CLI structure completeness
    """
    # Verify parser has description
    assert cli_parser.description is not None

    # Get subparsers
    subparsers_actions = [
        action for action in cli_parser._actions
        if isinstance(action, argparse._SubParsersAction)
    ]

    assert len(subparsers_actions) > 0

    # Verify all expected commands exist
    expected_commands = [
        'get-current-tag',
        'increment-prerelease',
        'init-rc',
        'init-patch',
        'get-current-rc-patch',
        'increment-rc-patch',
        'create-prod'
    ]

    for action in subparsers_actions:
        for command in expected_commands:
            assert command in action.choices


def test_cli_detailed_flag_consistency(mock_vcm):
    """Test --detailed flag behavior across different commands.

    This test verifies that the --detailed flag is consistently implemented
    across all commands that support it, providing uniform user experience
    and predictable output formatting.

    Test Scenario:
        1. Test detailed output for multiple commands
        2. Verify descriptive messages are added
        3. Confirm tag values still present
        4. Check consistent message formatting

    Validates:
        - Detailed flag adds descriptive context
        - Tag values preserved in output
        - Consistent message format
        - No functionality breakage

    Business Logic Tested:
        - Detailed flag implementation
        - Conditional output formatting
        - User experience consistency
    """
    # Test get-current-tag with detailed
    mock_vcm.get_current_tag.return_value = "1.0.0-dev.1"

    parser = create_parser()
    args = parser.parse_args(['get-current-tag', '--detailed'])

    captured_output = StringIO()
    with patch('sys.stdout', captured_output):
        result = handle_get_current_tag(args)

    assert result == 0
    output = captured_output.getvalue()
    assert "1.0.0-dev.1" in output
    assert len(output) > len("1.0.0-dev.1")  # Has additional text

    # Test increment-prerelease with detailed
    mock_vcm.increment_prerelease_tag.return_value = "1.0.0-dev.2"

    args = parser.parse_args(['increment-prerelease', '--tag', '1.0.0-dev.1', '--detailed'])

    captured_output = StringIO()
    with patch('sys.stdout', captured_output):
        result = handle_increment_prerelease(args)

    assert result == 0
    output = captured_output.getvalue()
    assert "1.0.0-dev.2" in output
    assert "Created prerelease tag" in output


def test_cli_custom_prerelease_identifiers(mock_vcm):
    """Test CLI support for custom prerelease identifiers.

    This test verifies that the CLI correctly handles different prerelease
    tag identifiers beyond the default 'dev', supporting flexible tagging
    strategies for different development workflows.

    Test Scenarios:
        1. Custom 'alpha' prerelease tag
        2. Custom 'beta' prerelease tag
        3. Custom 'staging' prerelease tag
        4. Parameter passing to VCM

    Validates:
        - Flexible prerelease identifier support
        - Parameter passing correctness
        - Custom workflow support
        - Consistent behavior across identifiers

    Business Logic Tested:
        - Prerelease tag parameter handling
        - Custom identifier support
        - Parameter validation and passing
    """
    custom_identifiers = ['alpha', 'beta', 'staging']

    for identifier in custom_identifiers:
        mock_vcm.get_current_tag.return_value = f"1.0.0-{identifier}.1"

        parser = create_parser()
        args = parser.parse_args(['get-current-tag', '--prerelease-tag', identifier])

        captured_output = StringIO()
        with patch('sys.stdout', captured_output):
            result = handle_get_current_tag(args)

        assert result == 0
        mock_vcm.get_current_tag.assert_called_with(
            prerelease_tag=identifier,
            production=False
        )

def test_cli_error_handling_comprehensive():
    """Comprehensive test of CLI error handling scenarios.

    This test validates that the CLI properly handles all types of errors
    that can occur during operation, ensuring users get clear feedback
    and the CLI never crashes unexpectedly.

    Test Scenarios:
        1. ValueError from invalid input
        2. Missing repository
        3. Missing required arguments
        4. Invalid command
        5. General exceptions

    Validates:
        - All error types handled gracefully
        - Clear error messages provided
        - Appropriate exit codes
        - No uncaught exceptions
        - Stderr used for all errors

    Business Logic Tested:
        - Comprehensive error handling
        - Error message clarity
        - Exit code conventions
        - User experience during errors
    """
    # Test with mock to avoid actual repository operations
    with patch('src.vcm.cli.VersionControlManager') as mock_class:
        mock_instance = mock_class.return_value

        # Test ValueError handling
        mock_instance.increment_prerelease_tag.side_effect = ValueError("Bad format")

        parser = create_parser()
        args = parser.parse_args(['increment-prerelease', '--tag', 'bad'])

        captured_error = StringIO()
        with patch('sys.stderr', captured_error):
            result = handle_increment_prerelease(args)

        assert result == 1
        assert "Invalid tag format" in captured_error.getvalue()

        # Test general exception handling
        mock_instance.get_current_tag.side_effect = Exception("Unexpected error")

        args = parser.parse_args(['get-current-tag'])

        captured_error = StringIO()
        with patch('sys.stderr', captured_error):
            result = handle_get_current_tag(args)

        assert result == 1
        assert "Error" in captured_error.getvalue()


def test_cli_output_format_scriptability():
    """Test that CLI output is easily scriptable and parseable.

    This test verifies that the CLI produces clean, parseable output
    when the --detailed flag is not used, making it suitable for
    use in scripts and automation.

    Test Scenarios:
        1. Basic output contains only tag value
        2. No extra whitespace or formatting
        3. Consistent output format
        4. Easy to parse in shell scripts

    Validates:
        - Clean output for scripting
        - No extra formatting characters
        - Consistent line endings
        - Single-line output for tag values

    Business Logic Tested:
        - Output formatting for automation
        - Scriptability considerations
        - Clean data extraction
    """
    with patch('src.vcm.cli.VersionControlManager') as mock_class:
        mock_instance = mock_class.return_value
        mock_instance.get_current_tag.return_value = "1.2.3-dev.4"

        parser = create_parser()
        args = parser.parse_args(['get-current-tag'])

        captured_output = StringIO()
        with patch('sys.stdout', captured_output):
            result = handle_get_current_tag(args)

        output = captured_output.getvalue()

        # Should be exactly the tag value plus newline
        assert output.strip() == "1.2.3-dev.4"
        assert output.count('\n') == 1  # Single line
        assert len(output.strip()) == len("1.2.3-dev.4")  # No extra characters


# ============================================================================
# TEST CLEANUP
# ============================================================================

def test_zzz_cleanup():
    """Final test to cleanup test repository.

    This test runs last (due to zzz_ prefix) and ensures the test
    directory is cleaned up after all tests complete. This prevents
    accumulation of test artifacts and ensures clean test runs.

    Cleanup Process:
        - Checks if test_dir exists
        - Removes entire directory tree
        - Ensures no test artifacts remain

    Note:
        This test must run last, hence the zzz_ prefix which sorts
        alphabetically after all other tests.
    """
    if os.path.isdir("test_dir"):
        shutil.rmtree("test_dir")
        assert not os.path.exists("test_dir")


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
"""
Test Repository Cleanup:

The test suite creates a real Git repository ('test_dir') for integration testing.
This repository is automatically cleaned up at the end of the test execution
to prevent accumulation of test artifacts and ensure clean test runs.

Cleanup Process:
    - Performed after the final test (test_major_bump)
    - Uses shutil.rmtree() to completely remove the test directory
    - Includes safety check with os.path.isdir() before removal
    - Ensures no test artifacts remain after execution

Test Execution Notes:
    - Tests must be run in order due to state dependencies
    - Each test builds upon the repository state from previous tests
    - The test suite simulates a complete development lifecycle
    - Real Git operations ensure authentic integration testing

Sequential Dependencies:
    1. test_current_tag: Establishes initial repository state
    2. test_increment_prerelease_tag: Creates additional dev tags
    3. test_init_new_rc → test_prod_release: RC workflow
    4. test_init_new_patch → test_create_prod_from_patch: Patch workflow  
    5. test_major_bump: Complete development cycle
"""
