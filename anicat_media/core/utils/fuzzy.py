"""
Fuzzy string matching utilities with fallback implementation.

This module provides a fuzzy matching class that uses thefuzz if available,
otherwise falls back to a pure Python implementation with the same API.

Usage:
    Basic usage with the convenience functions:

    >>> from anicat_media.core.utils.fuzzy import fuzz
    >>> fuzz.ratio("hello world", "hello")
    62
    >>> fuzz.partial_ratio("hello world", "hello")
    100

    Using the FuzzyMatcher class directly:

    >>> from anicat_media.core.utils.fuzzy import FuzzyMatcher
    >>> matcher = FuzzyMatcher()
    >>> matcher.backend
    'thefuzz'  # or 'pure_python' if thefuzz is not available
    >>> matcher.token_sort_ratio("fuzzy wuzzy", "wuzzy fuzzy")
    100

    For drop-in replacement of thefuzz.fuzz:

    >>> from anicat_media.core.utils.fuzzy import ratio, partial_ratio
    >>> ratio("test", "best")
    75
"""

import logging

logger = logging.getLogger(__name__)

# Try to import thefuzz, fall back to pure Python implementation
try:
    from thefuzz import fuzz as _fuzz_impl

    THEFUZZ_AVAILABLE = True
    logger.debug("Using thefuzz for fuzzy matching")
except ImportError:
    _fuzz_impl = None
    THEFUZZ_AVAILABLE = False
    logger.debug("thefuzz not available, using fallback implementation")


class _PurePythonFuzz:
    """
    Pure Python implementation of fuzzy string matching algorithms.

    This provides the same API as thefuzz.fuzz but with pure Python implementations
    of the core algorithms.
    """

    @staticmethod
    def _levenshtein_distance(s1: str, s2: str) -> int:
        """
        Calculate the Levenshtein distance between two strings.

        Args:
            s1: First string
            s2: Second string

        Returns:
            The Levenshtein distance as an integer
        """
        if len(s1) < len(s2):
            return _PurePythonFuzz._levenshtein_distance(s2, s1)

        if len(s2) == 0:
            return len(s1)

        previous_row = list(range(len(s2) + 1))
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                # Cost of insertions, deletions and substitutions
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row

        return previous_row[-1]

    @staticmethod
    def _longest_common_subsequence(s1: str, s2: str) -> int:
        """
        Calculate the length of the longest common subsequence.

        Args:
            s1: First string
            s2: Second string

        Returns:
            Length of the longest common subsequence
        """
        m, n = len(s1), len(s2)
        dp = [[0] * (n + 1) for _ in range(m + 1)]

        for i in range(1, m + 1):
            for j in range(1, n + 1):
                if s1[i - 1] == s2[j - 1]:
                    dp[i][j] = dp[i - 1][j - 1] + 1
                else:
                    dp[i][j] = max(dp[i - 1][j], dp[i][j - 1])

        return dp[m][n]

    @staticmethod
    def _normalize_string(s: str) -> str:
        """
        Normalize a string for comparison by converting to lowercase and stripping whitespace.

        Args:
            s: String to normalize

        Returns:
            Normalized string
        """
        return s.lower().strip()

    @staticmethod
    def ratio(s1: str, s2: str) -> int:
        """
        Calculate the similarity ratio between two strings using Levenshtein distance.

        Args:
            s1: First string
            s2: Second string

        Returns:
            Similarity ratio as an integer from 0 to 100
        """
        if not s1 and not s2:
            return 100
        if not s1 or not s2:
            return 0

        distance = _PurePythonFuzz._levenshtein_distance(s1, s2)
        max_len = max(len(s1), len(s2))

        if max_len == 0:
            return 100

        similarity = (max_len - distance) / max_len
        return int(similarity * 100)

    @staticmethod
    def partial_ratio(s1: str, s2: str) -> int:
        """
        Calculate the partial similarity ratio between two strings.

        This finds the best matching substring and calculates the ratio for that.

        Args:
            s1: First string
            s2: Second string

        Returns:
            Partial similarity ratio as an integer from 0 to 100
        """
        if not s1 or not s2:
            return 0

        if len(s1) <= len(s2):
            shorter, longer = s1, s2
        else:
            shorter, longer = s2, s1

        best_ratio = 0
        for i in range(len(longer) - len(shorter) + 1):
            substring = longer[i : i + len(shorter)]
            ratio = _PurePythonFuzz.ratio(shorter, substring)
            best_ratio = max(best_ratio, ratio)

        return best_ratio

    @staticmethod
    def token_sort_ratio(s1: str, s2: str) -> int:
        """
        Calculate similarity after sorting tokens in both strings.

        Args:
            s1: First string
            s2: Second string

        Returns:
            Token sort ratio as an integer from 0 to 100
        """
        if not s1 or not s2:
            return 0

        # Normalize and split into tokens
        tokens1 = sorted(_PurePythonFuzz._normalize_string(s1).split())
        tokens2 = sorted(_PurePythonFuzz._normalize_string(s2).split())

        # Rejoin sorted tokens
        sorted_s1 = " ".join(tokens1)
        sorted_s2 = " ".join(tokens2)

        return _PurePythonFuzz.ratio(sorted_s1, sorted_s2)

    @staticmethod
    def token_set_ratio(s1: str, s2: str) -> int:
        """
        Calculate similarity using set operations on tokens.

        Args:
            s1: First string
            s2: Second string

        Returns:
            Token set ratio as an integer from 0 to 100
        """
        if not s1 or not s2:
            return 0

        # Normalize and split into tokens
        tokens1 = set(_PurePythonFuzz._normalize_string(s1).split())
        tokens2 = set(_PurePythonFuzz._normalize_string(s2).split())

        # Find intersection and differences
        intersection = tokens1 & tokens2
        diff1 = tokens1 - tokens2
        diff2 = tokens2 - tokens1

        # Create sorted strings for comparison
        sorted_intersection = " ".join(sorted(intersection))
        sorted_diff1 = " ".join(sorted(diff1))
        sorted_diff2 = " ".join(sorted(diff2))

        # Combine strings for comparison
        combined1 = f"{sorted_intersection} {sorted_diff1}".strip()
        combined2 = f"{sorted_intersection} {sorted_diff2}".strip()

        if not combined1 and not combined2:
            return 100
        if not combined1 or not combined2:
            return 0

        return _PurePythonFuzz.ratio(combined1, combined2)

    @staticmethod
    def partial_token_sort_ratio(s1: str, s2: str) -> int:
        """
        Calculate partial similarity after sorting tokens.

        Args:
            s1: First string
            s2: Second string

        Returns:
            Partial token sort ratio as an integer from 0 to 100
        """
        if not s1 or not s2:
            return 0

        # Normalize and split into tokens
        tokens1 = sorted(_PurePythonFuzz._normalize_string(s1).split())
        tokens2 = sorted(_PurePythonFuzz._normalize_string(s2).split())

        # Rejoin sorted tokens
        sorted_s1 = " ".join(tokens1)
        sorted_s2 = " ".join(tokens2)

        return _PurePythonFuzz.partial_ratio(sorted_s1, sorted_s2)

    @staticmethod
    def partial_token_set_ratio(s1: str, s2: str) -> int:
        """
        Calculate partial similarity using set operations on tokens.

        Args:
            s1: First string
            s2: Second string

        Returns:
            Partial token set ratio as an integer from 0 to 100
        """
        if not s1 or not s2:
            return 0

        # Normalize and split into tokens
        tokens1 = set(_PurePythonFuzz._normalize_string(s1).split())
        tokens2 = set(_PurePythonFuzz._normalize_string(s2).split())

        # Find intersection and differences
        intersection = tokens1 & tokens2
        diff1 = tokens1 - tokens2
        diff2 = tokens2 - tokens1

        # Create sorted strings for comparison
        sorted_intersection = " ".join(sorted(intersection))
        sorted_diff1 = " ".join(sorted(diff1))
        sorted_diff2 = " ".join(sorted(diff2))

        # Combine strings for comparison
        combined1 = f"{sorted_intersection} {sorted_diff1}".strip()
        combined2 = f"{sorted_intersection} {sorted_diff2}".strip()

        if not combined1 and not combined2:
            return 100
        if not combined1 or not combined2:
            return 0

        return _PurePythonFuzz.partial_ratio(combined1, combined2)


class FuzzyMatcher:
    """
    Fuzzy string matching class with the same API as thefuzz.fuzz.

    This class automatically uses thefuzz if available, otherwise falls back
    to a pure Python implementation.
    """

    def __init__(self):
        """Initialize the fuzzy matcher with the appropriate backend."""
        if THEFUZZ_AVAILABLE and _fuzz_impl is not None:
            self._impl = _fuzz_impl
            self._backend = "thefuzz"
        else:
            self._impl = _PurePythonFuzz
            self._backend = "pure_python"

        logger.debug(f"FuzzyMatcher initialized with backend: {self._backend}")

    @property
    def backend(self) -> str:
        """Get the name of the backend being used."""
        return self._backend

    def ratio(self, s1: str, s2: str) -> int:
        """
        Calculate the similarity ratio between two strings.

        Args:
            s1: First string
            s2: Second string

        Returns:
            Similarity ratio as an integer from 0 to 100
        """
        try:
            return self._impl.ratio(s1, s2)
        except Exception as e:
            logger.warning(f"Error in ratio calculation: {e}")
            return 0

    def partial_ratio(self, s1: str, s2: str) -> int:
        """
        Calculate the partial similarity ratio between two strings.

        Args:
            s1: First string
            s2: Second string

        Returns:
            Partial similarity ratio as an integer from 0 to 100
        """
        try:
            return self._impl.partial_ratio(s1, s2)
        except Exception as e:
            logger.warning(f"Error in partial_ratio calculation: {e}")
            return 0

    def token_sort_ratio(self, s1: str, s2: str) -> int:
        """
        Calculate similarity after sorting tokens in both strings.

        Args:
            s1: First string
            s2: Second string

        Returns:
            Token sort ratio as an integer from 0 to 100
        """
        try:
            return self._impl.token_sort_ratio(s1, s2)
        except Exception as e:
            logger.warning(f"Error in token_sort_ratio calculation: {e}")
            return 0

    def token_set_ratio(self, s1: str, s2: str) -> int:
        """
        Calculate similarity using set operations on tokens.

        Args:
            s1: First string
            s2: Second string

        Returns:
            Token set ratio as an integer from 0 to 100
        """
        try:
            return self._impl.token_set_ratio(s1, s2)
        except Exception as e:
            logger.warning(f"Error in token_set_ratio calculation: {e}")
            return 0

    def partial_token_sort_ratio(self, s1: str, s2: str) -> int:
        """
        Calculate partial similarity after sorting tokens.

        Args:
            s1: First string
            s2: Second string

        Returns:
            Partial token sort ratio as an integer from 0 to 100
        """
        try:
            return self._impl.partial_token_sort_ratio(s1, s2)
        except Exception as e:
            logger.warning(f"Error in partial_token_sort_ratio calculation: {e}")
            return 0

    def partial_token_set_ratio(self, s1: str, s2: str) -> int:
        """
        Calculate partial similarity using set operations on tokens.

        Args:
            s1: First string
            s2: Second string

        Returns:
            Partial token set ratio as an integer from 0 to 100
        """
        try:
            return self._impl.partial_token_set_ratio(s1, s2)
        except Exception as e:
            logger.warning(f"Error in partial_token_set_ratio calculation: {e}")
            return 0

    def best_ratio(self, s1: str, s2: str) -> int:
        """
        Get the best ratio from all available methods.

        Args:
            s1: First string
            s2: Second string

        Returns:
            Best similarity ratio as an integer from 0 to 100
        """
        ratios = [
            self.ratio(s1, s2),
            self.partial_ratio(s1, s2),
            self.token_sort_ratio(s1, s2),
            self.token_set_ratio(s1, s2),
            self.partial_token_sort_ratio(s1, s2),
            self.partial_token_set_ratio(s1, s2),
        ]
        return max(ratios)


# Create a default instance for convenience
fuzz = FuzzyMatcher()

# Export the functions for drop-in replacement of thefuzz.fuzz
ratio = fuzz.ratio
partial_ratio = fuzz.partial_ratio
token_sort_ratio = fuzz.token_sort_ratio
token_set_ratio = fuzz.token_set_ratio
partial_token_sort_ratio = fuzz.partial_token_sort_ratio
partial_token_set_ratio = fuzz.partial_token_set_ratio

__all__ = [
    "FuzzyMatcher",
    "fuzz",
    "ratio",
    "partial_ratio",
    "token_sort_ratio",
    "token_set_ratio",
    "partial_token_sort_ratio",
    "partial_token_set_ratio",
    "THEFUZZ_AVAILABLE",
]
