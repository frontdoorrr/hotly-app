#!/bin/bash

# Test Automation Script for Hotly App
# Provides comprehensive test execution with different configurations

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
COVERAGE_THRESHOLD=80
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REPORT_DIR="${PROJECT_ROOT}/test-reports"

# Functions
print_header() {
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

cleanup() {
    if [ -f "${PROJECT_ROOT}/.coverage" ]; then
        rm "${PROJECT_ROOT}/.coverage"
    fi
}

setup_reports_dir() {
    mkdir -p "${REPORT_DIR}"
    mkdir -p "${REPORT_DIR}/coverage"
    mkdir -p "${REPORT_DIR}/junit"
}

check_dependencies() {
    print_header "Checking Dependencies"

    if ! command -v python &> /dev/null; then
        print_error "Python is not installed"
        exit 1
    fi

    if ! python -m pytest --version &> /dev/null; then
        print_error "pytest is not installed"
        print_info "Install with: pip install pytest pytest-cov pytest-asyncio"
        exit 1
    fi

    print_success "All dependencies are available"
}

run_unit_tests() {
    print_header "Running Unit Tests"

    python -m pytest tests/unit/ \
        --cov=app \
        --cov-report=term-missing \
        --cov-report=html:${REPORT_DIR}/coverage/unit \
        --cov-report=xml:${REPORT_DIR}/coverage/unit-coverage.xml \
        --junit-xml=${REPORT_DIR}/junit/unit-tests.xml \
        --tb=short \
        -v \
        || {
            print_error "Unit tests failed"
            return 1
        }

    print_success "Unit tests completed"
}

run_integration_tests() {
    print_header "Running Integration Tests"

    python -m pytest tests/integration/ \
        --cov=app \
        --cov-append \
        --cov-report=term-missing \
        --cov-report=html:${REPORT_DIR}/coverage/integration \
        --cov-report=xml:${REPORT_DIR}/coverage/integration-coverage.xml \
        --junit-xml=${REPORT_DIR}/junit/integration-tests.xml \
        --tb=short \
        -v \
        || {
            print_error "Integration tests failed"
            return 1
        }

    print_success "Integration tests completed"
}

run_e2e_tests() {
    print_header "Running End-to-End Tests"

    python -m pytest tests/e2e/ \
        --cov=app \
        --cov-append \
        --cov-report=term-missing \
        --cov-report=html:${REPORT_DIR}/coverage/e2e \
        --cov-report=xml:${REPORT_DIR}/coverage/e2e-coverage.xml \
        --junit-xml=${REPORT_DIR}/junit/e2e-tests.xml \
        --tb=short \
        -v \
        --maxfail=5 \
        || {
            print_error "E2E tests failed"
            return 1
        }

    print_success "E2E tests completed"
}

run_tdd_tests() {
    print_header "Running TDD Example Tests"

    python -m pytest tests/tdd/examples/ \
        --junit-xml=${REPORT_DIR}/junit/tdd-tests.xml \
        --tb=short \
        -v \
        || {
            print_error "TDD example tests failed"
            return 1
        }

    print_success "TDD example tests completed"
}

run_framework_tests() {
    print_header "Running Framework Tests"

    python -m pytest tests/framework/ \
        --junit-xml=${REPORT_DIR}/junit/framework-tests.xml \
        --tb=short \
        -v \
        || {
            print_error "Framework tests failed"
            return 1
        }

    print_success "Framework tests completed"
}

run_performance_tests() {
    print_header "Running Performance Tests"

    if [ -d "tests/performance" ]; then
        python -m pytest tests/performance/ \
            --junit-xml=${REPORT_DIR}/junit/performance-tests.xml \
            --tb=short \
            -v \
            || {
                print_warning "Performance tests failed"
                return 1
            }

        print_success "Performance tests completed"
    else
        print_info "No performance tests found, skipping"
    fi
}

check_coverage() {
    print_header "Checking Coverage"

    coverage report --show-missing --fail-under=${COVERAGE_THRESHOLD} || {
        print_error "Coverage below ${COVERAGE_THRESHOLD}%"
        return 1
    }

    print_success "Coverage meets requirements (≥${COVERAGE_THRESHOLD}%)"
}

generate_combined_report() {
    print_header "Generating Combined Coverage Report"

    coverage combine 2>/dev/null || true
    coverage html -d ${REPORT_DIR}/coverage/combined
    coverage xml -o ${REPORT_DIR}/coverage/combined-coverage.xml

    print_success "Combined coverage report generated"
    print_info "HTML report: ${REPORT_DIR}/coverage/combined/index.html"
}

run_linting() {
    print_header "Running Code Quality Checks"

    # Black formatting check
    if command -v black &> /dev/null; then
        print_info "Checking code formatting with Black"
        black --check --diff app tests || {
            print_warning "Code formatting issues found"
            print_info "Run 'black app tests' to fix formatting"
        }
    fi

    # isort import sorting check
    if command -v isort &> /dev/null; then
        print_info "Checking import sorting with isort"
        isort --check-only --diff app tests || {
            print_warning "Import sorting issues found"
            print_info "Run 'isort app tests' to fix imports"
        }
    fi

    # Flake8 linting
    if command -v flake8 &> /dev/null; then
        print_info "Checking code style with flake8"
        flake8 app tests || {
            print_warning "Code style issues found"
        }
    fi

    print_success "Code quality checks completed"
}

run_security_scan() {
    print_header "Running Security Scan"

    if command -v bandit &> /dev/null; then
        print_info "Running Bandit security scan"
        bandit -r app/ -f json -o ${REPORT_DIR}/bandit-report.json || {
            print_warning "Security issues found"
        }
        bandit -r app/ || true
    else
        print_info "Bandit not available, skipping security scan"
    fi

    if command -v safety &> /dev/null; then
        print_info "Running Safety dependency scan"
        safety check || {
            print_warning "Vulnerable dependencies found"
        }
    else
        print_info "Safety not available, skipping dependency scan"
    fi
}

show_help() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Test Automation Script for Hotly App"
    echo ""
    echo "Options:"
    echo "  -h, --help              Show this help message"
    echo "  -u, --unit              Run only unit tests"
    echo "  -i, --integration       Run only integration tests"
    echo "  -e, --e2e               Run only E2E tests"
    echo "  -p, --performance       Run only performance tests"
    echo "  -t, --tdd               Run only TDD example tests"
    echo "  -f, --framework         Run only framework tests"
    echo "  -q, --quality           Run only code quality checks"
    echo "  -s, --security          Run only security scans"
    echo "  -c, --coverage          Generate coverage report only"
    echo "  -a, --all               Run all tests (default)"
    echo "  --fast                  Run fast tests only (skip E2E and performance)"
    echo "  --ci                    Run in CI mode (optimized for CI/CD)"
    echo "  --threshold N           Set coverage threshold (default: 80)"
    echo ""
    echo "Examples:"
    echo "  $0                      # Run all tests"
    echo "  $0 --unit --coverage    # Run unit tests and generate coverage"
    echo "  $0 --fast              # Run fast tests only"
    echo "  $0 --ci                # Run in CI mode"
}

# Parse command line arguments
UNIT_ONLY=false
INTEGRATION_ONLY=false
E2E_ONLY=false
PERFORMANCE_ONLY=false
TDD_ONLY=false
FRAMEWORK_ONLY=false
QUALITY_ONLY=false
SECURITY_ONLY=false
COVERAGE_ONLY=false
FAST_MODE=false
CI_MODE=false
RUN_ALL=true

while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_help
            exit 0
            ;;
        -u|--unit)
            UNIT_ONLY=true
            RUN_ALL=false
            ;;
        -i|--integration)
            INTEGRATION_ONLY=true
            RUN_ALL=false
            ;;
        -e|--e2e)
            E2E_ONLY=true
            RUN_ALL=false
            ;;
        -p|--performance)
            PERFORMANCE_ONLY=true
            RUN_ALL=false
            ;;
        -t|--tdd)
            TDD_ONLY=true
            RUN_ALL=false
            ;;
        -f|--framework)
            FRAMEWORK_ONLY=true
            RUN_ALL=false
            ;;
        -q|--quality)
            QUALITY_ONLY=true
            RUN_ALL=false
            ;;
        -s|--security)
            SECURITY_ONLY=true
            RUN_ALL=false
            ;;
        -c|--coverage)
            COVERAGE_ONLY=true
            RUN_ALL=false
            ;;
        --fast)
            FAST_MODE=true
            RUN_ALL=false
            ;;
        --ci)
            CI_MODE=true
            ;;
        --threshold)
            COVERAGE_THRESHOLD="$2"
            shift
            ;;
        *)
            echo "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
    shift
done

# Main execution
main() {
    print_header "Hotly App Test Automation"
    print_info "Project root: ${PROJECT_ROOT}"
    print_info "Coverage threshold: ${COVERAGE_THRESHOLD}%"

    cd "${PROJECT_ROOT}"

    check_dependencies
    setup_reports_dir
    cleanup

    if [ "$COVERAGE_ONLY" = true ]; then
        generate_combined_report
        exit 0
    fi

    if [ "$QUALITY_ONLY" = true ]; then
        run_linting
        exit 0
    fi

    if [ "$SECURITY_ONLY" = true ]; then
        run_security_scan
        exit 0
    fi

    # Track test results
    FAILED_TESTS=()

    # Run tests based on options
    if [ "$RUN_ALL" = true ] || [ "$FAST_MODE" = true ]; then
        run_unit_tests || FAILED_TESTS+=("unit")
        run_integration_tests || FAILED_TESTS+=("integration")
        run_tdd_tests || FAILED_TESTS+=("tdd")
        run_framework_tests || FAILED_TESTS+=("framework")

        if [ "$FAST_MODE" = false ]; then
            run_e2e_tests || FAILED_TESTS+=("e2e")
            run_performance_tests || FAILED_TESTS+=("performance")
        fi

        check_coverage || FAILED_TESTS+=("coverage")
        generate_combined_report

        if [ "$CI_MODE" = false ]; then
            run_linting
            run_security_scan
        fi
    else
        # Run specific test types
        [ "$UNIT_ONLY" = true ] && (run_unit_tests || FAILED_TESTS+=("unit"))
        [ "$INTEGRATION_ONLY" = true ] && (run_integration_tests || FAILED_TESTS+=("integration"))
        [ "$E2E_ONLY" = true ] && (run_e2e_tests || FAILED_TESTS+=("e2e"))
        [ "$PERFORMANCE_ONLY" = true ] && (run_performance_tests || FAILED_TESTS+=("performance"))
        [ "$TDD_ONLY" = true ] && (run_tdd_tests || FAILED_TESTS+=("tdd"))
        [ "$FRAMEWORK_ONLY" = true ] && (run_framework_tests || FAILED_TESTS+=("framework"))

        # Generate coverage report if any tests were run
        if [ "$UNIT_ONLY" = true ] || [ "$INTEGRATION_ONLY" = true ] || [ "$E2E_ONLY" = true ]; then
            check_coverage || FAILED_TESTS+=("coverage")
            generate_combined_report
        fi
    fi

    # Final results
    print_header "Test Results Summary"

    if [ ${#FAILED_TESTS[@]} -eq 0 ]; then
        print_success "All tests passed! 🎉"
        print_info "Reports available in: ${REPORT_DIR}"
        exit 0
    else
        print_error "Some tests failed:"
        for test in "${FAILED_TESTS[@]}"; do
            print_error "  - $test"
        done
        print_info "Check reports in: ${REPORT_DIR}"
        exit 1
    fi
}

# Run main function
main "$@"
