import ast
import logging
from typing import Dict, List, Tuple, Optional
import re

logger = logging.getLogger(__name__)

class DirectiveValidator:
    def __init__(self, config: Dict):
        self.config = config
        self.forbidden_patterns = [
            r"os\.(system|popen|spawn|exec)",
            r"subprocess\.",
            r"eval\(",
            r"exec\(",
            r"__import__\(",
            r"open\([^)]*'w'",  # File writing
            r"requests?\.",     # Network requests
            r"socket\.",        # Socket operations
        ]
        self.max_complexity = 10

    def validate_directive(self, directive: Dict) -> Tuple[bool, Optional[str]]:
        """Validate a directive for safety and correctness"""
        if not all(k in directive for k in ['id', 'code', 'priority']):
            return False, "Missing required fields"

        # Validate code
        code_valid, code_msg = self.validate_code(directive['code'])
        if not code_valid:
            return False, code_msg

        # Validate priority
        if directive['priority'] not in ['Low', 'Medium', 'High', 'Critical']:
            return False, "Invalid priority level"

        return True, None

    def validate_code(self, code: str) -> Tuple[bool, Optional[str]]:
        """Validate code for safety and complexity"""
        # Check for forbidden patterns
        for pattern in self.forbidden_patterns:
            if re.search(pattern, code):
                return False, f"Contains forbidden pattern: {pattern}"

        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            return False, f"Syntax error: {str(e)}"

        # Check complexity
        complexity = self.calculate_complexity(tree)
        if complexity > self.max_complexity:
            return False, f"Code too complex (score: {complexity})"

        # Check for dangerous AST nodes
        dangerous_nodes = self.find_dangerous_nodes(tree)
        if dangerous_nodes:
            return False, f"Contains dangerous operations: {', '.join(dangerous_nodes)}"

        return True, None

    def calculate_complexity(self, tree: ast.AST) -> int:
        """Calculate cyclomatic complexity"""
        complexity = 1
        for node in ast.walk(tree):
            if isinstance(node, (ast.If, ast.While, ast.For, ast.FunctionDef,
                               ast.Try, ast.ExceptHandler)):
                complexity += 1
        return complexity

    def find_dangerous_nodes(self, tree: ast.AST) -> List[str]:
        """Find potentially dangerous AST nodes"""
        dangerous = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for name in node.names:
                    if name.name in ['os', 'sys', 'subprocess']:
                        dangerous.append(f'import {name.name}')
            elif isinstance(node, ast.Attribute):
                if isinstance(node.value, ast.Name):
                    attr = f"{node.value.id}.{node.attr}"
                    if any(re.match(pattern, attr) for pattern in self.forbidden_patterns):
                        dangerous.append(attr)
        return dangerous