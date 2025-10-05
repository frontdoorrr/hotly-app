#!/bin/bash
# ==============================================================================
# Docker Run Script for hotly-app
# ==============================================================================
# This script starts the hotly-app with Docker Compose
# ==============================================================================

set -e  # Exit on error

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Default values
COMPOSE_FILE="docker-compose.yml"
ENV_FILE=".env"
ACTION="up"
DETACH="-d"

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --dev|--development)
            COMPOSE_FILE="docker-compose.yml"
            ENV_FILE=".env"
            shift
            ;;
        --prod|--production)
            COMPOSE_FILE="docker-compose.prod.yml"
            ENV_FILE=".env.production"
            shift
            ;;
        --down|--stop)
            ACTION="down"
            shift
            ;;
        --logs)
            ACTION="logs"
            DETACH="-f"
            shift
            ;;
        --build)
            ACTION="up --build"
            shift
            ;;
        --no-detach|--foreground)
            DETACH=""
            shift
            ;;
        --help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --dev, --development     Use development configuration (default)"
            echo "  --prod, --production     Use production configuration"
            echo "  --down, --stop           Stop and remove containers"
            echo "  --logs                   Show container logs"
            echo "  --build                  Build images before starting"
            echo "  --no-detach              Run in foreground (don't detach)"
            echo "  --help                   Show this help message"
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            exit 1
            ;;
    esac
done

# Check if .env file exists
if [ "$ACTION" != "down" ] && [ "$ACTION" != "logs" ]; then
    if [ ! -f "$ENV_FILE" ]; then
        echo -e "${RED}Error: $ENV_FILE not found!${NC}"
        echo -e "${YELLOW}Please create $ENV_FILE from the template:${NC}"
        echo -e "  cp ${ENV_FILE}.example $ENV_FILE"
        echo -e "  # Edit $ENV_FILE and fill in your configuration"
        exit 1
    fi
fi

echo -e "${GREEN}===============================================================================${NC}"
echo -e "${GREEN}Docker Compose for hotly-app${NC}"
echo -e "${GREEN}===============================================================================${NC}"
echo -e "Compose file: ${YELLOW}$COMPOSE_FILE${NC}"
echo -e "Env file:     ${YELLOW}$ENV_FILE${NC}"
echo -e "Action:       ${YELLOW}$ACTION${NC}"
echo -e "${GREEN}===============================================================================${NC}"
echo ""

# Execute docker-compose command
if [ "$ACTION" == "down" ]; then
    echo -e "${YELLOW}▶ Stopping containers...${NC}"
    docker-compose -f "$COMPOSE_FILE" down
    echo -e "${GREEN}✓ Containers stopped${NC}"
elif [ "$ACTION" == "logs" ]; then
    echo -e "${YELLOW}▶ Showing logs...${NC}"
    docker-compose -f "$COMPOSE_FILE" logs $DETACH
else
    echo -e "${YELLOW}▶ Starting containers...${NC}"
    docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" $ACTION $DETACH

    if [ $? -eq 0 ]; then
        echo ""
        echo -e "${GREEN}===============================================================================${NC}"
        echo -e "${GREEN}✓ Containers started successfully!${NC}"
        echo -e "${GREEN}===============================================================================${NC}"
        echo -e "${YELLOW}API Server:${NC}     http://localhost:8000"
        echo -e "${YELLOW}API Docs:${NC}       http://localhost:8000/docs"
        echo -e "${YELLOW}Health Check:${NC}   http://localhost:8000/health"
        echo ""
        echo -e "${YELLOW}Useful commands:${NC}"
        echo -e "  View logs:        docker-compose -f $COMPOSE_FILE logs -f"
        echo -e "  Stop containers:  docker-compose -f $COMPOSE_FILE down"
        echo -e "  Restart:          docker-compose -f $COMPOSE_FILE restart"
        echo -e "  Enter shell:      docker-compose -f $COMPOSE_FILE exec app bash"
        echo ""
        echo -e "${YELLOW}Container status:${NC}"
        docker-compose -f "$COMPOSE_FILE" ps
    else
        echo -e "${RED}✗ Failed to start containers!${NC}"
        exit 1
    fi
fi
