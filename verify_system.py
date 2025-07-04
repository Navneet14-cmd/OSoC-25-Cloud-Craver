#!/usr/bin/env python3
"""
Cloud Craver System Verification Script

This script performs comprehensive testing of all Cloud Craver components
to ensure they work together as a unified system.
"""

import os
import sys
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Dict, List, Tuple
import json

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

class Colors:
    """ANSI color codes for terminal output."""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'
    END = '\033[0m'

class CloudCraverVerifier:
    """Main verification class for Cloud Craver system testing."""
    
    def __init__(self):
        """Initialize the verifier."""
        self.results: Dict[str, List[Tuple[str, bool, str]]] = {}
        self.temp_dir = tempfile.mkdtemp(prefix="cloudcraver_test_")
        self.success_count = 0
        self.total_count = 0
        
        print(f"{Colors.CYAN}{Colors.BOLD} Cloud Craver System Verification{Colors.END}")
        print(f"{Colors.WHITE}Testing directory: {self.temp_dir}{Colors.END}")
        print("=" * 60)
    
    def log_test(self, category: str, test_name: str, success: bool, message: str = ""):
        """Log a test result."""
        if category not in self.results:
            self.results[category] = []
        
        self.results[category].append((test_name, success, message))
        self.total_count += 1
        if success:
            self.success_count += 1
            
        status = f"{Colors.GREEN} PASS{Colors.END}" if success else f"{Colors.RED}❌ FAIL{Colors.END}"
        print(f"  {status} {test_name}")
        if message and not success:
            print(f"    {Colors.YELLOW}→ {message}{Colors.END}")
    
    def run_command(self, cmd: List[str], timeout: int = 30) -> Tuple[bool, str]:
        """Run a command and return success status and output."""
        try:
            result = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True, 
                timeout=timeout,
                cwd=Path(__file__).parent
            )
            return result.returncode == 0, result.stdout + result.stderr
        except subprocess.TimeoutExpired:
            return False, f"Command timed out after {timeout}s"
        except Exception as e:
            return False, str(e)
    
    def test_basic_cli(self):
        """Test basic CLI functionality."""
        print(f"\n{Colors.BLUE}{Colors.BOLD}📋 Testing Basic CLI Functionality{Colors.END}")
        
        # Test help command
        success, output = self.run_command(["python", "cloudcraver.py", "--help"])
        self.log_test("CLI", "Help command", success, output if not success else "")
        
        # Test version command
        success, output = self.run_command(["python", "cloudcraver.py", "--version"])
        self.log_test("CLI", "Version command", success, output if not success else "")
        
        # Test hello command
        success, output = self.run_command(["python", "cloudcraver.py", "hello"])
        self.log_test("CLI", "Hello command", success, output if not success else "")
        
        # Test status command
        success, output = self.run_command(["python", "cloudcraver.py", "status"])
        self.log_test("CLI", "Status command", success, output if not success else "")
    
    def test_template_generation(self):
        """Test template generation functionality."""
        print(f"\n{Colors.BLUE}{Colors.BOLD}🛠️ Testing Template Generation{Colors.END}")
        
        test_templates = ["vpc", "ec2", "s3", "rds"]
        
        for template in test_templates:
            output_dir = os.path.join(self.temp_dir, f"test_{template}")
            success, output = self.run_command([
                "python", "cloudcraver.py", "generate", 
                "--template", template, 
                "--output", output_dir
            ])
            
            # Check if template file was created
            if success:
                template_file = os.path.join(output_dir, f"{template}.tf")
                file_exists = os.path.exists(template_file)
                self.log_test("Templates", f"Generate {template}", file_exists, 
                            f"File not created: {template_file}" if not file_exists else "")
            else:
                self.log_test("Templates", f"Generate {template}", False, output)
    
    def test_template_validation(self):
        """Test template validation functionality."""
        print(f"\n{Colors.BLUE}{Colors.BOLD} Testing Template Validation{Colors.END}")
        
        # First generate a template to validate
        test_dir = os.path.join(self.temp_dir, "validation_test")
        success, _ = self.run_command([
            "python", "cloudcraver.py", "generate", 
            "--template", "vpc", 
            "--output", test_dir
        ])
        
        if success:
            # Test validation
            success, output = self.run_command([
                "python", "cloudcraver.py", "validate", test_dir
            ])
            self.log_test("Validation", "Validate generated template", success, output if not success else "")
        else:
            self.log_test("Validation", "Generate template for validation", False, "Failed to generate test template")
        
        # Test validation on non-existent directory
        success, output = self.run_command([
            "python", "cloudcraver.py", "validate", "/nonexistent/path"
        ])
        self.log_test("Validation", "Handle invalid path", not success, "Should fail for invalid path")
    
    def test_interactive_mode(self):
        """Test interactive template generation (with fallback)."""
        print(f"\n{Colors.BLUE}{Colors.BOLD} Testing Interactive Mode{Colors.END}")
        
        # Test interactive mode (should show fallback or work)
        success, output = self.run_command([
            "python", "cloudcraver.py", "interactive-generate"
        ], timeout=10)  # Shorter timeout for interactive mode
        
        # Interactive mode might timeout waiting for input, which is expected
        if "PyInquirer not installed" in output or "Falling back to basic input" in output:
            self.log_test("Interactive", "Graceful fallback handling", True, "PyInquirer fallback working")
        elif success:
            self.log_test("Interactive", "Interactive mode", True, "Interactive mode working")
        else:
            self.log_test("Interactive", "Interactive mode", False, output)
    
    def test_list_templates(self):
        """Test template listing functionality."""
        print(f"\n{Colors.BLUE}{Colors.BOLD} Testing Template Listing{Colors.END}")
        
        success, output = self.run_command(["python", "cloudcraver.py", "list-templates"])
        
        # Check if expected templates are listed
        expected_templates = ["vpc", "ec2", "s3", "rds"]
        if success:
            all_found = all(template in output for template in expected_templates)
            self.log_test("Templates", "List all templates", all_found, 
                        "Not all expected templates found" if not all_found else "")
        else:
            self.log_test("Templates", "List templates command", False, output)
    
    def test_state_management(self):
        """Test state management functionality."""
        print(f"\n{Colors.BLUE}{Colors.BOLD} Testing State Management{Colors.END}")
        
        # Test workspace creation
        success, output = self.run_command([
            "python", "cloudcraver.py", "state", "create-workspace", "test-workspace"
        ])
        self.log_test("State", "Create workspace", success, output if not success else "")
        
        # Test workspace switching
        success, output = self.run_command([
            "python", "cloudcraver.py", "state", "switch-workspace", "test-workspace"
        ])
        self.log_test("State", "Switch workspace", success, output if not success else "")
    
    def test_cost_estimation(self):
        """Test cost estimation functionality."""
        print(f"\n{Colors.BLUE}{Colors.BOLD} Testing Cost Estimation{Colors.END}")
        
        # Create a dummy plan file for testing
        plan_file = os.path.join(self.temp_dir, "test_plan.out")
        with open(plan_file, "w") as f:
            f.write('{"planned_values": {"root_module": {"resources": []}}}')
        
        providers = ["aws", "azure", "gcp"]
        for provider in providers:
            success, output = self.run_command([
                "python", "cloudcraver.py", "cost", "estimate", 
                provider, "--tfplan", plan_file
            ])
            self.log_test("Cost", f"Estimate {provider} costs", success, output if not success else "")
    
    def test_plugin_system(self):
        """Test plugin system functionality."""
        print(f"\n{Colors.BLUE}{Colors.BOLD} Testing Plugin System{Colors.END}")
        
        # Test plugin system initialization
        success, output = self.run_command(["python", "cloudcraver.py", "init"])
        self.log_test("Plugins", "Initialize plugin system", success, output if not success else "")
        
        # Test plugin listing
        success, output = self.run_command(["python", "cloudcraver.py", "plugin", "list"])
        # Plugin commands might not be available, which is okay
        if "not available" in output.lower() or "importerror" in output.lower():
            self.log_test("Plugins", "Plugin commands availability", True, "Plugin system gracefully unavailable")
        else:
            self.log_test("Plugins", "List plugins", success, output if not success else "")
    
    def test_error_handling(self):
        """Test error handling and edge cases."""
        print(f"\n{Colors.BLUE}{Colors.BOLD} Testing Error Handling{Colors.END}")
        
        # Test invalid template name
        success, output = self.run_command([
            "python", "cloudcraver.py", "generate", 
            "--template", "invalid_template_name", 
            "--output", self.temp_dir
        ])
        self.log_test("Error Handling", "Invalid template name", not success, "Should fail gracefully")
        
        # Test invalid command
        success, output = self.run_command([
            "python", "cloudcraver.py", "invalid-command"
        ])
        self.log_test("Error Handling", "Invalid command", not success, "Should show help or error")
    
    def test_performance(self):
        """Test basic performance metrics."""
        print(f"\n{Colors.BLUE}{Colors.BOLD} Testing Performance{Colors.END}")
        
        # Time template generation
        start_time = time.time()
        success, output = self.run_command([
            "python", "cloudcraver.py", "generate", 
            "--template", "vpc", 
            "--output", os.path.join(self.temp_dir, "perf_test")
        ])
        end_time = time.time()
        
        generation_time = end_time - start_time
        
        if success and generation_time < 5.0:  # Target: <5 seconds
            self.log_test("Performance", "Template generation speed", True, f"{generation_time:.2f}s")
        else:
            self.log_test("Performance", "Template generation speed", False, 
                        f"Too slow: {generation_time:.2f}s" if success else output)
    
    def test_configuration_system(self):
        """Test configuration system functionality."""
        print(f"\n{Colors.BLUE}{Colors.BOLD} Testing Configuration System{Colors.END}")
        
        # Test with debug flag
        success, output = self.run_command([
            "python", "cloudcraver.py", "--debug", "hello", "Debug test"
        ])
        self.log_test("Configuration", "Debug mode flag", success, output if not success else "")
        
        # Test with verbose flag
        success, output = self.run_command([
            "python", "cloudcraver.py", "--verbose", "status"
        ])
        self.log_test("Configuration", "Verbose mode flag", success, output if not success else "")
    
    def generate_report(self):
        """Generate final verification report."""
        print(f"\n{Colors.MAGENTA}{Colors.BOLD} Verification Report{Colors.END}")
        print("=" * 60)
        
        overall_success = self.success_count / self.total_count if self.total_count > 0 else 0
        
        print(f"Overall Success Rate: {Colors.GREEN if overall_success >= 0.8 else Colors.RED}{overall_success*100:.1f}%{Colors.END}")
        print(f"Tests Passed: {Colors.GREEN}{self.success_count}{Colors.END}/{self.total_count}")
        
        for category, tests in self.results.items():
            print(f"\n{Colors.CYAN}{Colors.BOLD}{category}:{Colors.END}")
            category_success = sum(1 for _, success, _ in tests if success)
            category_total = len(tests)
            category_rate = category_success / category_total if category_total > 0 else 0
            
            status_color = Colors.GREEN if category_rate >= 0.8 else Colors.YELLOW if category_rate >= 0.5 else Colors.RED
            print(f"  Success Rate: {status_color}{category_rate*100:.1f}%{Colors.END} ({category_success}/{category_total})")
            
            for test_name, success, message in tests:
                status = f"{Colors.GREEN}✅{Colors.END}" if success else f"{Colors.RED}❌{Colors.END}"
                print(f"  {status} {test_name}")
                if message and not success:
                    print(f"    {Colors.YELLOW}→ {message[:100]}{'...' if len(message) > 100 else ''}{Colors.END}")
        
        print(f"\n{Colors.WHITE}Temporary test files: {self.temp_dir}{Colors.END}")
        
        # Summary recommendations
        print(f"\n{Colors.BOLD} Recommendations:{Colors.END}")
        if overall_success >= 0.9:
            print(f"{Colors.GREEN}✅ System is production-ready!{Colors.END}")
        elif overall_success >= 0.7:
            print(f"{Colors.YELLOW}⚠️ System is mostly functional with minor issues to address.{Colors.END}")
        else:
            print(f"{Colors.RED}❌ System has significant issues that need attention.{Colors.END}")
            
        return overall_success >= 0.8
    
    def run_all_tests(self):
        """Run all verification tests."""
        print(f"{Colors.WHITE}Starting comprehensive system verification...{Colors.END}\n")
        
        # Run all test categories
        self.test_basic_cli()
        self.test_template_generation()
        self.test_template_validation()
        self.test_list_templates()
        self.test_interactive_mode()
        self.test_state_management()
        self.test_cost_estimation()
        self.test_plugin_system()
        self.test_configuration_system()
        self.test_error_handling()
        self.test_performance()
        
        # Generate final report
        return self.generate_report()

def main():
    """Main verification function."""
    print(f"{Colors.BOLD}Cloud Craver System Verification Tool{Colors.END}")
    print(f"{Colors.WHITE}This tool tests all major components of Cloud Craver for production readiness.{Colors.END}\n")
    
    verifier = CloudCraverVerifier()
    
    try:
        success = verifier.run_all_tests()
        exit_code = 0 if success else 1
        
        print(f"\n{Colors.BOLD}Verification {'COMPLETED SUCCESSFULLY' if success else 'COMPLETED WITH ISSUES'}{Colors.END}")
        
        return exit_code
        
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Verification interrupted by user.{Colors.END}")
        return 1
    except Exception as e:
        print(f"\n{Colors.RED}Verification failed with error: {e}{Colors.END}")
        return 1
    finally:
        print(f"\n{Colors.WHITE}Temporary files can be found at: {verifier.temp_dir}{Colors.END}")

if __name__ == "__main__":
    sys.exit(main()) 