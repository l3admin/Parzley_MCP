"""Smoke tests: package imports and tool registration."""

import unittest


class TestImports(unittest.TestCase):
    def test_server_and_tools_import_without_error(self) -> None:
        import parzley_mcp.server  # noqa: F401
        import parzley_mcp.tools  # noqa: F401


if __name__ == "__main__":
    unittest.main()
