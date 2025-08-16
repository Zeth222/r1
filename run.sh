#!/bin/bash

if [ -z "$UNISWAP_SUBGRAPH_URL" ]; then
  echo "Error: UNISWAP_SUBGRAPH_URL is not set. Please set it before running this script."
  exit 1
fi

python -m bot.main
