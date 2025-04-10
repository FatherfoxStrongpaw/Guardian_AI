import os
import difflib
import ast
import logging
import time
import shutil
import json

# Configure logging.
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s: %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("consolidated_code_analysis.log"),
    ],
)
logger = logging.getLogger("ConsolidatedCodeAnalysis")


def analyze_dependencies(file_path):
    """
    Analyze a Python file to extract its import dependencies.
    Returns a dictionary with keys:
      - 'modules': a list of modules imported.
      - 'names': a list of specific names imported.
    """
    dependencies = {"modules": set(), "names": set()}
    try:
        with open(file_path, "r") as f:
            source = f.read()
        tree = ast.parse(source, filename=file_path)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    dependencies["modules"].add(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    dependencies["modules"].add(node.module)
                for alias in node.names:
                    dependencies["names"].add(alias.name)
    except Exception as e:
        logger.error("Error analyzing dependencies for %s: %s", file_path, e)
    # Convert sets to lists.
    dependencies["modules"] = list(dependencies["modules"])
    dependencies["names"] = list(dependencies["names"])
    return dependencies


class ConsolidatedCodeAnalysis:
    def __init__(
        self, baseline_dir="baseline", staging_dir="staging", archive_dir="archive"
    ):
        """
        Initializes directories for:
          - baseline: approved code.
          - staging: new or updated code awaiting review.
          - archive: backup for old versions.
        """
        self.baseline_dir = baseline_dir
        self.staging_dir = staging_dir
        self.archive_dir = archive_dir
        os.makedirs(baseline_dir, exist_ok=True)
        os.makedirs(staging_dir, exist_ok=True)
        os.makedirs(archive_dir, exist_ok=True)

    def get_all_files(self, root_dir, extension=".py"):
        """
        Recursively traverse the given root_dir and return a set of relative file paths
        for files that match the extension.
        """
        file_set = set()
        for dirpath, _, filenames in os.walk(root_dir):
            for filename in filenames:
                if filename.endswith(extension):
                    full_path = os.path.join(dirpath, filename)
                    rel_path = os.path.relpath(full_path, root_dir)
                    file_set.add(rel_path)
        return file_set

    def read_file_lines(self, filepath):
        """
        Read the file content as a list of lines.
        """
        if os.path.exists(filepath):
            with open(filepath, "r") as f:
                return f.readlines()
        return []

    def analyze_directory_diffs(self):
        """
        Compare all Python files between baseline and staging directories.
        Returns a dictionary mapping relative file paths to their diff (if any).
        """
        baseline_files = self.get_all_files(self.baseline_dir)
        staging_files = self.get_all_files(self.staging_dir)
        all_files = baseline_files.union(staging_files)
        diff_report = {}

        for rel_path in sorted(all_files):
            baseline_path = os.path.join(self.baseline_dir, rel_path)
            staging_path = os.path.join(self.staging_dir, rel_path)
            baseline_lines = self.read_file_lines(baseline_path)
            staging_lines = self.read_file_lines(staging_path)

            diff = list(
                difflib.unified_diff(
                    baseline_lines,
                    staging_lines,
                    fromfile=f"baseline/{rel_path}",
                    tofile=f"staging/{rel_path}",
                    lineterm="",
                )
            )
            if diff:
                diff_report[rel_path] = diff
                logger.info("Differences found in '%s':\n%s", rel_path, "\n".join(diff))
            else:
                logger.info("No differences in '%s'.", rel_path)
        return diff_report

    def analyze_dependencies_in_directory(self, root_dir):
        """
        Recursively analyze all Python files in the given directory for dependencies.
        Returns a dictionary mapping relative file paths to their dependency info.
        """
        dependency_report = {}
        all_files = self.get_all_files(root_dir)
        for rel_path in sorted(all_files):
            full_path = os.path.join(root_dir, rel_path)
            dependency_report[rel_path] = analyze_dependencies(full_path)
        return dependency_report

    def generate_aggregated_report(self):
        """
        Generate an aggregated report that includes:
          - Diff reports for files with differences.
          - Dependency mappings for baseline and staging directories.
        Returns a dictionary with the aggregated data.
        """
        diff_report = self.analyze_directory_diffs()
        baseline_deps = self.analyze_dependencies_in_directory(self.baseline_dir)
        staging_deps = self.analyze_dependencies_in_directory(self.staging_dir)
        report = {
            "timestamp": time.time(),
            "diff_report": diff_report,
            "baseline_dependencies": baseline_deps,
            "staging_dependencies": staging_deps,
        }
        logger.info("Aggregated multi-file diff and dependency report generated.")
        return report

    def archive_baseline_file(self, rel_path):
        """
        Archive the current baseline file for a given relative path.
        """
        baseline_file = os.path.join(self.baseline_dir, rel_path)
        if os.path.exists(baseline_file):
            archive_file = os.path.join(
                self.archive_dir,
                f"{rel_path.replace(os.sep, '_')}_baseline_{int(time.time())}.py",
            )
            os.makedirs(os.path.dirname(archive_file), exist_ok=True)
            shutil.copy2(baseline_file, archive_file)
            logger.info("Archived baseline file '%s' to '%s'.", rel_path, archive_file)

    def approve_change(self, rel_path):
        """
        Approve the new code for a specific file by archiving the current baseline
        and moving the staged file into the baseline directory.
        """
        staging_file = os.path.join(self.staging_dir, rel_path)
        baseline_file = os.path.join(self.baseline_dir, rel_path)
        if os.path.exists(staging_file):
            self.archive_baseline_file(rel_path)
            os.makedirs(os.path.dirname(baseline_file), exist_ok=True)
            shutil.move(staging_file, baseline_file)
            logger.info("Approved new code for '%s' and updated baseline.", rel_path)
        else:
            logger.warning("No staged file found for '%s' to approve.", rel_path)

    def reject_change(self, rel_path):
        """
        Reject the new code for a specific file by removing it from the staging area.
        """
        staging_file = os.path.join(self.staging_dir, rel_path)
        if os.path.exists(staging_file):
            os.remove(staging_file)
            logger.info(
                "Rejected new code for '%s' and removed it from staging.", rel_path
            )
        else:
            logger.warning("No staged file found for '%s' to reject.", rel_path)


# Example usage for testing.
if __name__ == "__main__":
    cca = ConsolidatedCodeAnalysis()
    aggregated_report = cca.generate_aggregated_report()
    print("Aggregated Report:")
    print(json.dumps(aggregated_report, indent=4))

    # For demonstration: auto-approve changes for any file with differences.
    for rel_path, diff in aggregated_report.get("diff_report", {}).items():
        if diff:
            logger.info("Auto-approving changes for '%s' (demo mode).", rel_path)
            cca.approve_change(rel_path)
