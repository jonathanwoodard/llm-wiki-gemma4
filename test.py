import unittest
import os
import shutil
import tempfile
import json
from unittest.mock import MagicMock, patch

# Import the components to be tested
# Note: Ensure tools.py and main.py are in the same directory
import tools
import main

class TestTools(unittest.TestCase):
    def setUp(self):
        """Create a temporary directory for file operations."""
        self.test_dir = tempfile.mkdtemp()
        # We need to patch is_safe_path or ensure our test_dir is within the CWD 
        # for the security check to pass. Since mkdtemp creates it in /tmp 
        # or similar, we'll manually adjust the logic for the test.
        self.safe_path = os.path.join(os.getcwd(), self.test_dir)
        os.makedirs(self.safe_path, exist_ok=True)

    def tearDown(self):
        """Clean up the temporary directory."""
        shutil.rmtree(self.safe_path)

    def test_write_and_read_file(self):
        """Test that writing and reading a file works correctly."""
        file_path = os.path.join(self.safe_path, "test.txt")
        content = "Hello World"
        
        # We patch is_safe_path to allow writing to our temp directory
        with patch('tools.is_safe_path', return_value=True):
            tools.write_file(file_path, content)
            read_content = tools.read_file(file_path)
            self.assertEqual(read_content, content)

    def test_write_file_frontmatter_validation(self):
        """Test that wiki files must start with YAML frontmatter."""
        file_path = os.path.join(self.safe_path, "wiki_test.md")
        invalid_content = "No frontmatter here"
        
        with patch('tools.is_safe_path', return.value=True):
            result = tools.write_file(file_path, invalid_content)
            self.assertIn("Error: Wiki files must start with YAML frontmatter", result)

    def test_append_to_file(self):
        """Test appending content to an existing file."""
        file_path = os.path.join(self.safe_path, "append_test.txt")
        with patch('tools.is_safe_path', return_value=True):
            tools.write_file(file_path, "Line 1\n")
            tools.append_to_file(file_path, "Line 2")
            content = tools.read_file(file_path)
            self.assertEqual(content.strip(), "Line 1\nLine 2")

    def test_search_wiki(self):
        """Test searching for text within markdown files."""
        wiki_dir = os.path.join(self.safe_path, "wiki")
        os.makedirs(wiki_dir)
        file1 = os.path.join(wiki_dir, "page1.md")
        file2 = os.path.join(wiki_dir, "page2.md")
        
        with patch('tools.is_safe_path', return_value=True):
            tools.write_file(file1, "This is about apples.")
            tools.write_file(file2, "This is about oranges.")
            
            result = tools.search_wiki("apples", root_dir=wiki_dir)
            self.assertIn("page1.md", result)
            self.assertNotIn("page2.md", result)

    def test_get_file_metadata(self):
        """Test extraction of YAML frontmatter."""
        file_path = os.path.join(self.safe_path, "meta.md")
        content = "---\ntitle: Test\nauthor: Agent\n---"
        
        with patch('tools.is_safe_path', return_value=True):
            tools.write_file(file_path, content)
            metadata = tools.get_file_metadata(file_path)
            self.assertIn("title: Test", metadata)
            self.assertIn("author: Agent", metadata)

class TestAgentLogic(unittest.TestCase):
    def setUp(self):
        # Initialize AgentRunner with a dummy model
        self.runner = main.AgentRunner(model_name="test-model")

    def test_parse_llm_output_valid(self):
        """Test parsing a correctly formatted LLM response."""
        llm_text = (
            "Thought: I need to read the file.\n"
            "Action: read_file\n"
            "Input: {\"path\": \"test.txt\"}\n"
            "Response: I have read the file."
        )
        parsed = self.runner.parse_llm_output(llm_text)
        
        self.assertEqual(parsed["thought"], "I need to read the file.")
        self.assertEqual(parsed["action"], "read_file")
        self.assertEqual(parsed["input"], "{\"path\": \"test.txt\"}")
        self.assertEqual(parsed["response"], "I have read the file.")

    def test_parse_llm_output_malformed(self):
        """Test parsing when the LLM fails to follow the format."""
        llm_text = "Just a random sentence without structure."
        parsed = self.runner.parse_llm_output(llm_text)
        
        self.assertIsNone(parsed["thought"])
        self.assertIsNone(parsed["action"])

    def test_execute_tool_success(self):
        """Test executing a registered tool."""
        # Mock the tool function
        mock_tool = MagicMock(return_value="Mock Success")
        self.runner.tool_registry["test_tool"] = mock_tool
        
        result = self.runner.execute_tool("test_tool", json.dumps({"param": "value"}))
        
        self.assertEqual(result, "Mock Success")
        mock_tool.assert_called_once_with(param="value")

    def test_execute_tool_invalid_name(self):
        """Test executing a non-existent tool."""
        result = self.runner.execute_tool("non_existent_tool", "{}")
        self.assertIn("Error: Tool 'non_existent_tool' is not registered", result)

    def test_execute_tool_invalid_json(self):
        """Test executing a tool with invalid JSON input."""
        result = self.runner.execute_tool("read_file", "not a json string")
        self.assertIn("Error", result)

if __name__ == "__main__":
    unittest.main()
